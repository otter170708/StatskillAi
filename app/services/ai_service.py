import os
import json
import random
import re
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from app.config import settings

# Custom-material quizzes always target Gemini Flash structured output.
GEMINI_CUSTOM_MATERIAL_MODEL = "gemini-2.5-flash"

class AIService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL_NAME or GEMINI_CUSTOM_MATERIAL_MODEL

    def shuffle_question_options(self, q: Dict[str, Any]) -> Dict[str, Any]:
        """
        Randomizes the order of options (A, B, C, D) while maintaining exact
        semantic alignment for correct_option and distractor_analysis.
        """
        q_type = (q.get("question_type") or "mcq").strip().lower()
        orig_options = q.get("options", {}) or {}
        orig_correct = str(q.get("correct_option", "A")).strip()
        orig_distractors = q.get("distractor_analysis", {}) or {}

        # Keep True/False and non-MCQ keys stable so the UI answer keys still match.
        if q_type != "mcq" or len(orig_options) < 2:
            return q
        option_labels = {k.strip().upper() for k in orig_options.keys()}
        if option_labels <= {"TRUE", "FALSE"}:
            return q

        orig_correct = orig_correct.upper()

        # Build list of option items
        items = []
        for key, text in orig_options.items():
            k_upper = key.strip().upper()
            is_correct = (k_upper == orig_correct)
            distractor_text = orig_distractors.get(key, orig_distractors.get(k_upper, ""))
            items.append({
                "orig_key": k_upper,
                "text": text,
                "is_correct": is_correct,
                "distractor_reason": distractor_text
            })

        # Randomize order
        random.shuffle(items)

        option_keys = ["A", "B", "C", "D"][:len(items)]
        new_options = {}
        new_correct_option = "A"
        new_distractors = {}

        for opt_key, item in zip(option_keys, items):
            new_options[opt_key] = item["text"]
            if item["is_correct"]:
                new_correct_option = opt_key
            else:
                if item["distractor_reason"]:
                    new_distractors[opt_key] = item["distractor_reason"]

        q_copy = dict(q)
        q_copy["options"] = new_options
        q_copy["correct_option"] = new_correct_option
        q_copy["distractor_analysis"] = new_distractors
        return q_copy

    @staticmethod
    def _is_configured_api_key(key: Optional[str]) -> bool:
        if not key or not isinstance(key, str):
            return False
        cleaned = key.strip()
        if not cleaned or cleaned.startswith("your_") or "placeholder" in cleaned.lower() or len(cleaned) < 15:
            return False
        return True

    async def generate_mcqs(
        self,
        context_text: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        role_target: str = "Junior Statistical Officer",
        excluded_scenario_hashes: Optional[List[str]] = None,
        format_type: str = "mcq"  # "mcq", "true_false", or "mixed"
    ) -> List[Dict[str, Any]]:
        question_type = self._normalize_generation_type(format_type)

        # Uploaded custom material → Gemini 2.5 Flash structured JSON
        # Only call remote API when an authentic, non-placeholder API key is configured
        if self._is_configured_api_key(self.api_key):
            try:
                raw_qs = await self._call_gemini_api(
                    context_text, num_questions, difficulty, role_target, question_type
                )
                return self._finalize_questions(raw_qs, question_type)
            except Exception as e:
                print(f"Warning: Live AI call failed ({e}). Falling back to material-based questions.")

        raw_qs = self._generate_local_fallback(
            context_text, num_questions, difficulty, role_target,
            excluded_scenario_hashes, question_type
        )
        return self._finalize_questions(raw_qs, question_type)

    def _normalize_generation_type(self, format_type: Optional[str]) -> str:
        t = (format_type or "mcq").strip().lower().replace("-", "_").replace(" ", "_")
        if t in {"true_false", "truefalse", "tf"}:
            return "true_false"
        if t == "mixed":
            return "mixed"
        return "mcq"

    def _is_mixed_format(self, format_type: Optional[str]) -> bool:
        return self._normalize_generation_type(format_type) == "mixed"

    def _generate_local_fallback(
        self,
        context_text: str,
        num_questions: int,
        difficulty: str,
        role_target: str,
        excluded_scenario_hashes: Optional[List[str]],
        question_type: str,
    ) -> List[Dict[str, Any]]:
        if question_type == "mixed":
            return self._generate_domain_mock_mixed(
                context_text, num_questions, difficulty, role_target, excluded_scenario_hashes
            )
        if question_type == "true_false":
            return self._generate_domain_mock_mixed(
                context_text, num_questions, difficulty, role_target, excluded_scenario_hashes
            )
        return self._generate_material_based_mcqs(
            context_text, num_questions, difficulty, role_target, excluded_scenario_hashes
        )

    def _extract_material_chunks(self, context: str) -> List[str]:
        """Split uploaded material into usable fact sentences."""
        if not context or not str(context).strip():
            return []
        cleaned = re.sub(r"-{2,}\s*Page\s+\d+\s*-{2,}", " ", str(context), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        chunks = []
        seen = set()
        for part in parts:
            sentence = part.strip(" \n\t-•*")
            if len(sentence) < 50 or len(sentence) > 420:
                continue
            key = sentence.lower()[:90]
            if key in seen:
                continue
            seen.add(key)
            chunks.append(sentence)
        if len(chunks) < 2 and len(cleaned) >= 80:
            # Fall back to paragraph-sized slices when sentence splitting is weak
            for i in range(0, len(cleaned), 220):
                slice_text = cleaned[i:i + 220].strip()
                if len(slice_text) >= 50:
                    chunks.append(slice_text)
        return chunks

    def _clip_option(self, text: str, limit: int = 220) -> str:
        text = (text or "").strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1].rsplit(" ", 1)[0] + "…"

    def _looks_like_true_false(self, q: Dict[str, Any]) -> bool:
        q_type = (q.get("question_type") or "").strip().lower()
        if q_type in {"true_false", "true/false", "tf"}:
            return True
        options = q.get("options") or {}
        if len(options) != 2:
            return False
        labels = {str(k).strip().lower() for k in options.keys()}
        values = {str(v).strip().lower() for v in options.values()}
        tf_tokens = {"true", "false"}
        return labels <= tf_tokens or values <= tf_tokens

    def _coerce_to_four_option_mcq(self, q: Dict[str, Any], fallback_chunks: Optional[List[str]] = None) -> Dict[str, Any]:
        """Force a question into a 4-option MCQ so MCQ quizzes never render as True/False."""
        q = dict(q)
        statement = (q.get("question_text") or q.get("scenario_text") or "").strip()
        options = dict(q.get("options") or {})
        if not self._looks_like_true_false(q) and len(options) >= 4:
            q["question_type"] = "mcq"
            if "question_text" not in q or not q.get("question_text"):
                q["question_text"] = "Which of the following is the most appropriate action based on the uploaded material?"
            return q

        extras = list(fallback_chunks or [])
        distractors = [
            "Ignore the uploaded guidance and proceed using informal field practice.",
            "Replace the recorded values with neighboring unit averages without documentation.",
            "Skip validation because the respondent verbally confirmed the figure.",
        ]
        for extra in extras:
            clipped = self._clip_option(extra)
            if clipped and clipped.lower() not in {statement.lower(), *(d.lower() for d in distractors)}:
                distractors.insert(0, clipped)
        correct = self._clip_option(statement) if statement else "Follow the procedure described in the uploaded training material."
        q["question_type"] = "mcq"
        q["question_text"] = "According to the uploaded material, which statement is correct?"
        q["scenario_text"] = q.get("scenario_text") or "Use only the uploaded training material to choose the valid official-statistics practice."
        q["options"] = {
            "A": correct,
            "B": self._clip_option(distractors[0]),
            "C": self._clip_option(distractors[1]),
            "D": self._clip_option(distractors[2]),
        }
        q["correct_option"] = "A"
        q["distractor_analysis"] = {
            "B": "This contradicts the uploaded material and official scrutiny norms.",
            "C": "Undocumented substitution introduces non-sampling bias.",
            "D": "Skipping validation violates data quality requirements in the source material.",
        }
        return q

    def _finalize_questions(self, raw_qs: Any, question_type: str) -> List[Dict[str, Any]]:
        if isinstance(raw_qs, dict):
            raw_qs = raw_qs.get("questions") or raw_qs.get("items") or [raw_qs]
        questions = [q for q in (raw_qs or []) if isinstance(q, dict)]
        requested = self._normalize_generation_type(question_type if isinstance(question_type, str) else ("mixed" if question_type else "mcq"))
        finalized = []
        for q in questions:
            item = dict(q)
            if requested == "mcq":
                item = self._coerce_to_four_option_mcq(item)
                if not self._validate_mcq_format(item):
                    print(f"Warning: Question {item.get('question_id', 'unknown')} failed MCQ validation. Skipping.")
                    continue
            else:
                item["question_type"] = (item.get("question_type") or requested).strip().lower()
            if not item.get("question_text"):
                item["question_text"] = "Which of the following is the most appropriate action based on the uploaded material?"
            finalized.append(self.shuffle_question_options(item))
        return finalized

    def _validate_mcq_format(self, q: Dict[str, Any]) -> bool:
        """Validate that a question is properly formatted as a 4-option MCQ."""
        # Check question type
        q_type = (q.get("question_type") or "").strip().lower()
        if q_type and q_type != "mcq":
            print(f"Invalid question type: {q_type}. Expected 'mcq'.")
            return False
        
        # Check options exist and are exactly 4
        options = q.get("options") or {}
        if len(options) != 4:
            print(f"Invalid number of options: {len(options)}. Expected 4.")
            return False
        
        # Check option keys are A, B, C, D
        expected_keys = {"A", "B", "C", "D"}
        actual_keys = set(str(k).upper() for k in options.keys())
        if actual_keys != expected_keys:
            print(f"Invalid option keys: {actual_keys}. Expected {expected_keys}.")
            return False
        
        # Check that options are not True/False
        option_values = [str(v).strip().lower() for v in options.values()]
        tf_indicators = {"true", "false"}
        for value in option_values:
            if value in tf_indicators:
                print(f"Option contains True/False indicator: {value}. MCQs should not use True/False.")
                return False
        
        # Check that correct_option is valid
        correct = q.get("correct_option", "").strip().upper()
        if correct not in expected_keys:
            print(f"Invalid correct_option: {correct}. Must be one of {expected_keys}.")
            return False
        
        return True

    def _generate_material_based_mcqs(
        self,
        context: str,
        num_questions: int,
        difficulty: str,
        role_target: str,
        excluded_scenario_hashes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate MCQs strictly based on uploaded material content."""
        chunks = self._extract_material_chunks(context)
        excluded = set(excluded_scenario_hashes or [])
        
        if not chunks:
            # Fallback to domain-specific questions if material extraction fails
            return self._generate_domain_mock_mcqs(
                context, num_questions, difficulty, role_target, excluded_scenario_hashes
            )
        
        generic_wrong = [
            "Impute missing or inconsistent values immediately without field verification or remarks.",
            "Substitute the unit with the nearest convenient respondent on the same day.",
            "Drop the record from the sample to keep the dataset looking internally consistent.",
            "Publish identifiable respondent details so the estimate can be independently audited.",
        ]
        bloom = "Analysis" if (difficulty or "").lower() == "hard" else "Application"
        questions = []
        order = list(range(len(chunks)))
        random.shuffle(order)
        
        for idx in order:
            if len(questions) >= num_questions:
                break
            fact = chunks[idx]
            if fact[:40] in excluded:
                continue
            other = [chunks[j] for j in range(len(chunks)) if j != idx]
            random.shuffle(other)
            distractor_texts = [self._clip_option(x) for x in other[:3]]
            while len(distractor_texts) < 3:
                distractor_texts.append(generic_wrong[len(distractor_texts) % len(generic_wrong)])
            questions.append({
                "question_id": f"Q{len(questions) + 1}",
                "question_type": "mcq",
                "competency_mapped": "OSS-STAT-06",
                "bloom_taxonomy_level": bloom,
                "scenario_text": fact,
                "question_text": "According to the uploaded material, which of the following statements is correct?",
                "options": {
                    "A": self._clip_option(fact),
                    "B": distractor_texts[0],
                    "C": distractor_texts[1],
                    "D": distractor_texts[2],
                },
                "correct_option": "A",
                "explanation": f"The uploaded material states: {fact}",
                "distractor_analysis": {
                    "B": "This statement is not supported by the uploaded material.",
                    "C": "This statement is not supported by the uploaded material.",
                    "D": "This statement is not supported by the uploaded material.",
                },
            })

        if len(questions) < num_questions:
            needed = num_questions - len(questions)
            extra = self._generate_domain_mock_mcqs(
                context, needed, difficulty, role_target, excluded_scenario_hashes
            )
            for q in extra:
                q_copy = dict(q)
                q_copy["question_id"] = f"Q{len(questions) + 1}"
                questions.append(q_copy)
                if len(questions) >= num_questions:
                    break

        return questions

    def _get_master_prompt(self, context_text: str, num_questions: int, difficulty: str, role_target: str, format_type: str = "mcq") -> str:
        if self._is_mixed_format(format_type):
            return f"""You are a Senior Assessment Specialist for India's Official Statistical System (MoSPI / iGOT Karmayogi).

TASK:
Generate exactly {num_questions} practical, scenario-based questions with MIXED formats strictly grounded in the training context provided below.

TARGET ROLE: {role_target}
DIFFICULTY: {difficulty} (Bloom's Taxonomy: Application & Analysis)

CONTEXT MATERIAL:
{context_text[:12000]}

QUESTION TYPES TO INCLUDE (mix these in your response):
- Multiple Choice Questions (MCQ) with A, B, C, D options
- True/False questions
- Fill in the Blank questions
- Match the Following questions
- Short Answer questions
- Essay-type questions

MAPPING RULES:
- Map each question to one of these Competency IDs:
  * OSS-STAT-01: Survey Methodology & Sampling Frame Design
  * OSS-STAT-02: Field Scrutiny & Schedule Validation
  * OSS-STAT-03: Outlier Detection & Imputation Techniques
  * OSS-STAT-04: Non-Sampling Error Minimization
  * OSS-STAT-05: Data Quality Assurance & Audit Trails
  * OSS-STAT-06: Official Statistics Standards & MoSPI Guidelines
  * OSS-STAT-07: Data Privacy, Confidentiality & Anonymization
  * OSS-STAT-08: Consumer Price Index & Index Numbers Compilation
  * OSS-STAT-09: National Accounts & Gross State Domestic Product (GSDP)
  * OSS-STAT-10: Statistical Dissemination & Dashboard Visualization

REQUIREMENTS:
1. Every question MUST present a realistic official workplace scenario.
2. For MCQs: Ensure correct answer positions are randomly distributed across A, B, C, and D.
3. For True/False: Provide clear "True" or "False" answer with explanation.
4. For Fill in the Blank: Provide the exact word/phrase answer and explanation.
5. For Match the Following: Provide pairs and correct mapping.
6. For Short Answer/Essay: Provide sample answer guidelines and explanation.
7. Provide detailed explanations for all question types.
8. Output MUST be valid JSON array with no extra markdown wrapping.

JSON SCHEMA:
[
  {{
    "question_id": "Q1",
    "question_type": "mcq",  // "mcq", "true_false", "fill_blank", "match", "short_answer", "essay"
    "competency_mapped": "OSS-STAT-02",
    "bloom_taxonomy_level": "Application",
    "scenario_text": "Scenario description...",
    "question_text": "Actual question...",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "correct_option": "C",
    "explanation": "Detailed rationale...",
    "distractor_analysis": {{
      "A": "Why A is incorrect...",
      "B": "Why B is incorrect...",
      "D": "Why D is incorrect..."
    }}
  }}
]
"""
        else:
            return f"""You are a Senior Assessment Specialist for India's Official Statistical System (MoSPI / iGOT Karmayogi).

TASK:
Generate exactly {num_questions} practical, scenario-based Multiple Choice Questions (MCQs) strictly grounded in the training context provided below.

TARGET ROLE: {role_target}
DIFFICULTY: {difficulty} (Bloom's Taxonomy: Application & Analysis)

CONTEXT MATERIAL:
{context_text[:8000]}

MAPPING RULES:
- Map each question to one of these Competency IDs:
  * OSS-STAT-01: Survey Methodology & Sampling Frame Design
  * OSS-STAT-02: Field Scrutiny & Schedule Validation
  * OSS-STAT-03: Outlier Detection & Imputation Techniques
  * OSS-STAT-04: Non-Sampling Error Minimization
  * OSS-STAT-05: Data Quality Assurance & Audit Trails
  * OSS-STAT-06: Official Statistics Standards & MoSPI Guidelines
  * OSS-STAT-07: Data Privacy, Confidentiality & Anonymization
  * OSS-STAT-08: Consumer Price Index & Index Numbers Compilation
  * OSS-STAT-09: National Accounts & Gross State Domestic Product (GSDP)
  * OSS-STAT-10: Statistical Dissemination & Dashboard Visualization

REQUIREMENTS:
1. Every question MUST be grounded in the CONTEXT MATERIAL. Use facts from that text; do not invent unrelated items.
2. Generate ONLY four-option MCQs. Do NOT generate true/false, fill-in-the-blank, match, short-answer, or essay items.
3. Options A, B, C, and D must be distinct substantive statements. Never use True/False as the option set.
4. Ensure correct answer positions are randomly distributed across A, B, C, and D.
5. Provide a detailed distractor analysis explaining the specific misconception for each incorrect option.
6. Output MUST be valid JSON array with no extra markdown wrapping. Each object MUST include question_type "mcq" and question_text.

JSON SCHEMA:
[
  {{
    "question_id": "Q1",
    "question_type": "mcq",
    "competency_mapped": "OSS-STAT-02",
    "bloom_taxonomy_level": "Application",
    "scenario_text": "Scenario description...",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "correct_option": "C",
    "explanation": "Detailed rationale...",
    "distractor_analysis": {{
      "A": "Why A is incorrect...",
      "B": "Why B is incorrect...",
      "D": "Why D is incorrect..."
    }}
  }}
]
"""

    def _gemini_option_map_schema(self, required_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """A/B/C/D (+ True/False) string map. Gemini rejects additionalProperties."""
        properties = {
            "A": {"type": "STRING"},
            "B": {"type": "STRING"},
            "C": {"type": "STRING"},
            "D": {"type": "STRING"},
            "True": {"type": "STRING"},
            "False": {"type": "STRING"},
        }
        schema: Dict[str, Any] = {
            "type": "OBJECT",
            "properties": properties,
            "propertyOrdering": list(properties.keys()),
        }
        if required_keys:
            schema["required"] = required_keys
        return schema

    def _gemini_question_item_schema(self, question_type: str) -> Dict[str, Any]:
        """JSON schema matching app.schemas.QuestionSchema (generation fields only)."""
        if question_type == "mcq":
            type_enum = ["mcq"]
            options_schema = self._gemini_option_map_schema(["A", "B", "C", "D"])
            correct_enum = ["A", "B", "C", "D"]
            required = [
                "question_id", "question_type", "competency_mapped", "bloom_taxonomy_level",
                "scenario_text", "question_text", "options", "correct_option", "explanation",
                "distractor_analysis",
            ]
        elif question_type == "true_false":
            type_enum = ["true_false"]
            options_schema = self._gemini_option_map_schema(["True", "False"])
            correct_enum = ["True", "False", "A", "B"]
            required = [
                "question_id", "question_type", "competency_mapped", "bloom_taxonomy_level",
                "scenario_text", "question_text", "options", "correct_option", "explanation",
            ]
        else:
            type_enum = ["mcq", "true_false", "fill_blank", "match", "short_answer", "essay"]
            options_schema = self._gemini_option_map_schema()
            correct_enum = ["A", "B", "C", "D", "True", "False"]
            required = [
                "question_id", "question_type", "competency_mapped", "bloom_taxonomy_level",
                "scenario_text", "question_text", "correct_option", "explanation",
            ]

        properties = {
            "question_id": {"type": "STRING"},
            "competency_mapped": {"type": "STRING"},
            "bloom_taxonomy_level": {"type": "STRING"},
            "question_type": {"type": "STRING", "enum": type_enum},
            "scenario_text": {"type": "STRING"},
            "question_text": {"type": "STRING"},
            "options": options_schema,
            "match_pairs": self._gemini_option_map_schema(),
            "match_column_b": {"type": "ARRAY", "items": {"type": "STRING"}},
            "fill_blank_prompt": {"type": "STRING"},
            "essay_guidelines": {"type": "STRING"},
            "allow_upload": {"type": "BOOLEAN"},
            "correct_option": {"type": "STRING", "enum": correct_enum},
            "explanation": {"type": "STRING"},
            "distractor_analysis": self._gemini_option_map_schema(),
            "review_status": {"type": "STRING", "enum": ["APPROVED", "PENDING", "NEEDS_REVISION"]},
        }
        return {
            "type": "OBJECT",
            "properties": properties,
            "required": required,
            "propertyOrdering": list(properties.keys()),
        }

    def _gemini_questions_response_schema(self, question_type: str) -> Dict[str, Any]:
        return {
            "type": "OBJECT",
            "properties": {
                "questions": {
                    "type": "ARRAY",
                    "items": self._gemini_question_item_schema(question_type),
                }
            },
            "required": ["questions"],
            "propertyOrdering": ["questions"],
        }

    def _custom_material_prompt(
        self,
        context_text: str,
        num_questions: int,
        question_type: str,
        difficulty: str,
        role_target: str,
    ) -> str:
        material = (context_text or "").strip()[:15000]
        shared = f"""You are a Senior Assessment Specialist for India's Official Statistical System (MoSPI / iGOT Karmayogi).

TARGET ROLE: {role_target}
DIFFICULTY: {difficulty}

UPLOADED MATERIAL (the only allowed source of facts):
{material}

GROUNDING RULES (mandatory):
- Generate questions ONLY from the uploaded material above.
- Do not use outside knowledge, prior training facts, or invented statistics.
- If a fact is not in the material, do not ask about it.
- Every explanation must cite or paraphrase the material, not general knowledge.

Map competency_mapped to one of: OSS-STAT-01, OSS-STAT-02, OSS-STAT-03, OSS-STAT-04, OSS-STAT-05, OSS-STAT-06, OSS-STAT-07, OSS-STAT-08, OSS-STAT-09, OSS-STAT-10.
Set review_status to APPROVED.
"""
        if question_type == "mcq":
            return shared + f"""
TASK: Generate exactly {num_questions} multiple-choice questions.

MCQ RULES:
- question_type must be "mcq" for every item.
- Each question MUST have exactly 4 options in fields A, B, C, D.
- Mark exactly one correct answer in correct_option (A, B, C, or D).
- Options must be distinct, substantive statements drawn from the material.
- Do NOT write true/false, yes/no, or trivial two-choice questions.
- Do NOT use True/False as option text.
- Distractors must be plausible misreadings of the material, not obviously silly.
- Spread correct_option across A/B/C/D.
- Fill distractor_analysis for every incorrect option.
"""
        if question_type == "true_false":
            return shared + f"""
TASK: Generate exactly {num_questions} true/false questions.

TRUE/FALSE RULES:
- question_type must be "true_false".
- options must include keys True and False.
- correct_option must be True or False.
- The statement in question_text must be verifiable from the uploaded material only.
"""
        return shared + f"""
TASK: Generate exactly {num_questions} mixed-format questions grounded only in the material.

Include a mix of mcq, true_false, fill_blank, match, short_answer, and essay as appropriate.
For any mcq item: exactly 4 options A-D, one correct_option, no true/false-style choices.
"""

    def build_gemini_custom_material_request(
        self,
        context_text: str,
        question_type: str,
        num_questions: int,
        difficulty: str = "medium",
        role_target: str = "Junior Statistical Officer",
    ) -> Dict[str, Any]:
        """Build Gemini generateContent payload: prompt + structured responseSchema.

        Plug-in: `_call_gemini_api` sends this payload to
        models/gemini-2.5-flash:generateContent. `generate_mcqs` calls that
        when AI_PROVIDER is gemini (or an API key is present).
        """
        normalized = self._normalize_generation_type(question_type)
        prompt = self._custom_material_prompt(
            context_text, num_questions, normalized, difficulty, role_target
        )
        response_schema = self._gemini_questions_response_schema(normalized)
        model = GEMINI_CUSTOM_MATERIAL_MODEL
        return {
            "model": model,
            "prompt": prompt,
            "response_schema": response_schema,
            "generation_config": {
                "temperature": settings.AI_TEMPERATURE if settings.AI_TEMPERATURE else 0.2,
                "maxOutputTokens": max(settings.AI_MAX_TOKENS or 2048, 4096),
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
            },
        }

    def _build_gemini_structured_output_request(
        self,
        context_text: str,
        num_questions: int,
        question_type: str,
        difficulty: str,
        role_target: str,
    ) -> Dict[str, Any]:
        return self.build_gemini_custom_material_request(
            context_text=context_text,
            question_type=question_type,
            num_questions=num_questions,
            difficulty=difficulty,
            role_target=role_target,
        )

    async def _call_gemini_api(self, context: str, n: int, diff: str, role: str, format_type: str = "mcq") -> List[Dict[str, Any]]:
        # Plug-in point: custom-material quizzes use structured Gemini output.
        request_data = self.build_gemini_custom_material_request(
            context_text=context,
            question_type=format_type,
            num_questions=n,
            difficulty=diff,
            role_target=role,
        )
        model = request_data["model"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": request_data["prompt"]}]}],
            "generationConfig": request_data["generation_config"],
        }

        max_retries = 2
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(url, json=payload)

                if res.status_code == 429:
                    if attempt < max_retries - 1:
                        backoff_time = 2 ** attempt
                        print(f"Rate limited by Gemini API. Retrying in {backoff_time} seconds...")
                        await asyncio.sleep(backoff_time)
                        continue
                    raise HTTPException(
                        status_code=429,
                        detail="Gemini API rate limit exceeded. Please try again later or upgrade your API plan."
                    )

                if res.status_code >= 400:
                    print(f"Gemini structured-output error {res.status_code}: {res.text[:800]}")
                res.raise_for_status()
                data = res.json()
                parts = (
                    data.get("candidates") or [{}]
                )[0].get("content", {}).get("parts") or [{}]
                raw_text = parts[0].get("text") or "{}"
                parsed_response = json.loads(raw_text)
                if isinstance(parsed_response, list):
                    return parsed_response
                questions = parsed_response.get("questions", [])
                if not questions:
                    print("Warning: No questions returned from Gemini API")
                    return []
                return questions
        return []

    async def _call_openai_api(self, context: str, n: int, diff: str, role: str, format_type: str = "mcq") -> List[Dict[str, Any]]:
        prompt = self._get_master_prompt(context, n, diff, role, format_type)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model if "gpt" in self.model else "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_text = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_text)
            return parsed.get("questions", parsed) if isinstance(parsed, dict) else parsed

    async def _call_anthropic_api(self, context: str, n: int, diff: str, role: str, format_type: str = "mcq") -> List[Dict[str, Any]]:
        prompt = self._get_master_prompt(context, n, diff, role, format_type)
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model if "claude" in self.model else "claude-3-5-sonnet-20241022",
            "max_tokens": 2500,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt + "\nRespond with ONLY valid JSON array."}]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_text = data["content"][0]["text"].strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
            return json.loads(raw_text)

    def _generate_domain_mock_mixed(
        self,
        context: str,
        num_questions: int,
        difficulty: str,
        role_target: str,
        excluded_scenario_hashes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate mixed-format questions (MCQ, True/False, Fill-in-blank, Match, Short Answer, Essay)
        based on the uploaded material context.
        """
        chunks = self._extract_material_chunks(context)
        excluded = set(excluded_scenario_hashes or [])
        usable_chunks = [c for c in chunks if c[:40] not in excluded]
        if not usable_chunks:
            usable_chunks = list(chunks)
        random.shuffle(usable_chunks)

        context_lower = context.lower()
        key_terms = []
        if "sampling" in context_lower: key_terms.extend(["sampling", "sample size", "sampling frame"])
        if "survey" in context_lower: key_terms.extend(["survey", "questionnaire", "enumeration"])
        if "data" in context_lower: key_terms.extend(["data quality", "data validation", "data collection"])
        if "price" in context_lower or "index" in context_lower: key_terms.extend(["price index", "inflation", "CPI"])
        if "gdp" in context_lower or "national accounts" in context_lower: key_terms.extend(["GDP", "national accounts", "economic growth"])
        if not key_terms:
            key_terms = ["statistical methods", "data analysis", "official statistics"]

        mixed_pool = []
        question_types = ["mcq", "true_false", "fill_blank", "match", "short_answer", "essay"]
        material_mcqs = self._mcqs_from_material_chunks(
            usable_chunks, num_questions, difficulty, role_target, excluded_scenario_hashes
        )

        for i in range(num_questions):
            q_type = question_types[i % len(question_types)]
            term = key_terms[i % len(key_terms)]
            excerpt = usable_chunks[i % len(usable_chunks)] if usable_chunks else term
            
            if q_type == "mcq":
                if material_mcqs:
                    sourced = dict(material_mcqs.pop(0))
                    sourced["question_id"] = f"Q{i+1}"
                    mixed_pool.append(sourced)
                    continue
                mixed_pool.append({
                    "question_id": f"Q{i+1}",
                    "question_type": "mcq",
                    "competency_mapped": "OSS-STAT-02",
                    "bloom_taxonomy_level": "Application",
                    "scenario_text": excerpt if usable_chunks else f"In the context of {term} as described in the uploaded material.",
                    "question_text": f"Which method is recommended for {term} in official statistical practice?",
                    "options": {
                        "A": f"Random sampling without consideration of {term} principles",
                        "B": f"Systematic approach following {term} guidelines",
                        "C": f"Ad-hoc methods based on individual preference",
                        "D": f"Skipping {term} validation entirely"
                    },
                    "correct_option": "B",
                    "explanation": f"Official statistical guidelines mandate systematic approaches for {term} to ensure consistency and reliability.",
                    "distractor_analysis": {
                        "A": "Random approaches lack the systematic rigor required for official statistics.",
                        "C": "Ad-hoc methods introduce variability and reduce comparability.",
                        "D": "Skipping validation compromises data quality and official standards."
                    }
                })
            
            elif q_type == "true_false":
                mixed_pool.append({
                    "question_id": f"Q{i+1}",
                    "question_type": "true_false",
                    "competency_mapped": "OSS-STAT-05",
                    "bloom_taxonomy_level": "Comprehension",
                    "scenario_text": excerpt if usable_chunks else f"In the context of {term} as described in the uploaded material.",
                    "question_text": f"True or False: {term} validation should be performed only after data collection is complete.",
                    "options": {
                        "True": "True",
                        "False": "False"
                    },
                    "correct_option": "False",
                    "explanation": f"{term} validation should be an ongoing process throughout data collection, not just at the end.",
                    "distractor_analysis": {
                        "True": "Waiting until the end prevents real-time quality control and error correction."
                    }
                })
            
            elif q_type == "fill_blank":
                mixed_pool.append({
                    "question_id": f"Q{i+1}",
                    "question_type": "fill_blank",
                    "competency_mapped": "OSS-STAT-01",
                    "bloom_taxonomy_level": "Knowledge",
                    "scenario_text": f"Based on the material's discussion of {term}.",
                    "question_text": f"The primary purpose of _______ in {term} is to ensure data reliability and accuracy.",
                    "options": {
                        "answer": "validation"
                    },
                    "correct_option": "validation",
                    "explanation": f"Validation is essential in {term} to maintain data quality standards.",
                    "distractor_analysis": {}
                })
            
            elif q_type == "match":
                mixed_pool.append({
                    "question_id": f"Q{i+1}",
                    "question_type": "match",
                    "competency_mapped": "OSS-STAT-03",
                    "bloom_taxonomy_level": "Analysis",
                    "scenario_text": f"Match the following {term} concepts with their correct descriptions.",
                    "question_text": "Match each term with its appropriate definition.",
                    "options": {
                        "A": "Data cleaning",
                        "B": "Outlier detection",
                        "C": "Imputation",
                        "D": "Validation"
                    },
                    "match_pairs": {
                        "A": "Removing errors and inconsistencies",
                        "B": "Identifying unusual values",
                        "C": "Estimating missing values",
                        "D": "Verifying data accuracy"
                    },
                    "correct_option": "A-C, B-B, C-A, D-D",
                    "explanation": f"Proper matching of {term} concepts is fundamental for statistical analysis.",
                    "distractor_analysis": {}
                })
            
            elif q_type == "short_answer":
                mixed_pool.append({
                    "question_id": f"Q{i+1}",
                    "question_type": "short_answer",
                    "competency_mapped": "OSS-STAT-04",
                    "bloom_taxonomy_level": "Application",
                    "scenario_text": f"Based on the material's coverage of {term}.",
                    "question_text": f"Explain the key challenges in implementing {term} in official statistics and suggest one mitigation strategy.",
                    "options": {},
                    "correct_option": "Sample answer should address implementation challenges and propose specific mitigation.",
                    "explanation": f"Successful {term} implementation requires addressing technical, procedural, and resource challenges.",
                    "distractor_analysis": {}
                })
            
            elif q_type == "essay":
                mixed_pool.append({
                    "question_id": f"Q{i+1}",
                    "question_type": "essay",
                    "competency_mapped": "OSS-STAT-06",
                    "bloom_taxonomy_level": "Evaluation",
                    "scenario_text": f"Considering the material's discussion of {term} in the context of official statistical standards.",
                    "question_text": f"Write a comprehensive essay discussing the importance of {term} in maintaining public trust in official statistics. Include specific examples from the material and discuss potential consequences of poor implementation.",
                    "options": {},
                    "correct_option": "Essay should demonstrate understanding of {term} principles, official standards, and impact on statistical credibility.",
                    "explanation": f"{term} is fundamental to maintaining the integrity and credibility of official statistics.",
                    "distractor_analysis": {},
                    "allow_upload": True
                })
        
        return mixed_pool

    def _generate_domain_mock_mcqs(
        self,
        context: str,
        num_questions: int,
        difficulty: str,
        role_target: str,
        excluded_scenario_hashes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extensive pool of 20+ realistic MoSPI / NSSO / ASI / Price Statistics / CAPI
        scenarios across all 10 Official Statistical System competencies.
        Prefer questions built from uploaded material when the document has readable text.
        """
        full_pool = [
            # 1. Field Scrutiny & Schedule Validation (OSS-STAT-02)
            {
                "pool_id": "POOL-01",
                "competency_mapped": "OSS-STAT-02",
                "bloom_taxonomy_level": "Application",
                "scenario_text": "During an annual enterprise survey, an investigator encounters a reporting manufacturing unit with high sales output but zero electricity expenditure recorded in Schedule Block 4. What is the mandatory standard operating procedure?",
                "options": {
                    "A": "Immediately impute the electricity cost based on the median expenditure of neighboring units in the same district.",
                    "B": "Record zero expenditure as reported and submit the schedule without remarks.",
                    "C": "Conduct on-site physical verification for captive energy sources (e.g., solar or captive generator) and document remarks in Schedule Block 3.",
                    "D": "Delete the enterprise record from the sample and replace it with a substitute unit immediately."
                },
                "correct_option": "C",
                "explanation": "Official MoSPI field scrutiny guidelines mandate physical verification of captive generation before any data imputation can occur.",
                "distractor_analysis": {
                    "A": "Imputing values prematurely without field scrutiny introduces synthetic bias and masks captive power generation.",
                    "B": "Failing to document explanatory notes for abnormal energy expenditure violates data validation norms.",
                    "D": "Sample substitution is only permissible after formal casualty declaration protocols and supervisory approval."
                }
            },
            # 2. Survey Methodology & Sampling Frame Design (OSS-STAT-01)
            {
                "pool_id": "POOL-02",
                "competency_mapped": "OSS-STAT-01",
                "bloom_taxonomy_level": "Analysis",
                "scenario_text": "In a nationwide multistage socioeconomic survey, a field supervisor observes that several sample households in a First Stage Unit (FSU) were locked during the first visit. Which protocol must be strictly observed?",
                "options": {
                    "A": "Immediately substitute the locked households with the nearest available neighbor on the same day.",
                    "B": "Mandate at least TWO additional re-visits on different days and times before categorizing the unit as a Casualty.",
                    "C": "Collect proxy data from the local village panchayat representative.",
                    "D": "Drop the entire FSU from the sample frame."
                },
                "correct_option": "B",
                "explanation": "NSSO standard operating procedures require at least 2 re-visits on distinct dates to minimize non-response bias before declaring casualty.",
                "distractor_analysis": {
                    "A": "Immediate substitution creates convenience bias and over-represents easily available respondents.",
                    "C": "Proxy data collection for household consumer expenditure is strictly prohibited under survey protocols.",
                    "D": "Dropping whole sampling units compromises the stratified probability weights of the survey."
                }
            },
            # 3. Outlier Detection & Imputation Techniques (OSS-STAT-03)
            {
                "pool_id": "POOL-03",
                "competency_mapped": "OSS-STAT-03",
                "bloom_taxonomy_level": "Evaluation",
                "scenario_text": "A dataset of monthly rural household food expenditures reveals an isolated value exceeding the district median by 5.2 standard deviations. As a Statistical Officer, what is the best statistical approach?",
                "options": {
                    "A": "Automatically replace the value with the arithmetic mean of the entire state dataset.",
                    "B": "Delete the observation from the dataset without documenting the modification.",
                    "C": "Verify the itemized schedule breakdown for ceremonial or bulk purchase anomalies; if genuine, retain with outlier weighting adjustments.",
                    "D": "Round down the expenditure to match the 95th percentile value without investigation."
                },
                "correct_option": "C",
                "explanation": "Statistical best practices require checking itemized schedules (e.g. social ceremonies) and using principled outlier weighting rather than arbitrary deletion.",
                "distractor_analysis": {
                    "A": "Unchecked mean substitution artificially shrinks survey variance and standard errors.",
                    "B": "Silent deletion creates an unrecorded audit gap and non-sampling bias.",
                    "D": "Arbitrary Winsorization without domain verification distorts true economic inequality indicators."
                }
            },
            # 4. Data Quality Assurance & Audit Trails (OSS-STAT-05)
            {
                "pool_id": "POOL-04",
                "competency_mapped": "OSS-STAT-05",
                "bloom_taxonomy_level": "Application",
                "scenario_text": "During Computer-Assisted Personal Interviewing (CAPI) data entry, the tablet triggers a 'Hard Check' when a respondent's age is entered as 14 with marital status 'Widowed with 3 Children'. What does a Hard Check signify?",
                "options": {
                    "A": "A soft warning that can be bypassed by typing a supervisor note.",
                    "B": "An unresolvable logical contradiction that prevents schedule submission until corrected with verified data.",
                    "C": "An automated alert sent to the Ministry for real-time investigation.",
                    "D": "A system bug requiring app re-installation."
                },
                "correct_option": "B",
                "explanation": "In CAPI protocols, a Hard Check indicates an impossible logical inconsistency that strictly halts form progression until reconciled.",
                "distractor_analysis": {
                    "A": "Soft checks allow explanatory remarks; hard checks strictly block submission to prevent corrupt database entries.",
                    "C": "Hard checks are handled on-device at the time of enumerator interview, not as external ministerial alerts.",
                    "D": "Validation rules are intended behavioral constraints, not software failures."
                }
            },
            # 5. Data Privacy & Confidentiality (OSS-STAT-07)
            {
                "pool_id": "POOL-05",
                "competency_mapped": "OSS-STAT-07",
                "bloom_taxonomy_level": "Understanding",
                "scenario_text": "Under Section 9 of the Collection of Statistics Act, 2008, how must individual respondent microdata collected in official surveys be handled prior to public dissemination?",
                "options": {
                    "A": "Published with full name and Aadhaar details for open transparency.",
                    "B": "Shared with commercial marketing firms upon payment of prescribed fees.",
                    "C": "Strictly anonymized using k-anonymity masking and suppression of direct geographic identifiers below district level.",
                    "D": "Exempt from privacy regulations once aggregated to state level."
                },
                "correct_option": "C",
                "explanation": "The Collection of Statistics Act legally mandates complete confidentiality of respondent identifiers with algorithmic anonymization before public release.",
                "distractor_analysis": {
                    "A": "Disclosing personal identity details is a severe legal violation punishable under the Statistics Act.",
                    "B": "Official statistical data cannot be sold for commercial targeting under national privacy norms.",
                    "D": "Microdata release always requires privacy safeguards regardless of geographic aggregation."
                }
            },
            # 6. Non-Sampling Error Minimization (OSS-STAT-04)
            {
                "pool_id": "POOL-06",
                "competency_mapped": "OSS-STAT-04",
                "bloom_taxonomy_level": "Application",
                "scenario_text": "In a Consumer Expenditure Survey, respondents frequently under-report expenditure on durable goods when asked about a 30-day recall period. What methodological adjustment is prescribed to counter recall lapse?",
                "options": {
                    "A": "Extend the recall period to 365 days (Modified Mixed Reference Period - MMRP) for low-frequency durable purchases.",
                    "B": "Double the reported values during database post-processing.",
                    "C": "Ignore durable goods purchases altogether.",
                    "D": "Survey only upper-income households for durable items."
                },
                "correct_option": "A",
                "explanation": "The Modified Mixed Reference Period (MMRP) uses a 365-day recall for durables and infrequent expenses to prevent memory decay.",
                "distractor_analysis": {
                    "B": "Arbitrary doubling without empirical foundation introduces severe estimation errors.",
                    "C": "Omitting durable consumption leads to severe underestimation of aggregate living standards.",
                    "D": "Restricting samples to upper-income strata invalidates national representation."
                }
            },
            # 7. Official Statistics Standards (OSS-STAT-06)
            {
                "pool_id": "POOL-07",
                "competency_mapped": "OSS-STAT-06",
                "bloom_taxonomy_level": "Application",
                "scenario_text": "An enterprise produces solar panels and also undertakes residential electrical installation services. Under the National Industrial Classification (NIC 2008), how should the primary 5-digit NIC code be determined?",
                "options": {
                    "A": "By the activity that generated the maximum Gross Value Added (or turnover/employment) during the reference year.",
                    "B": "By whichever activity the owner started first historically.",
                    "C": "By splitting the enterprise into two separate legal entities in the sample frame.",
                    "D": "By assigning a random generic manufacturing code."
                },
                "correct_option": "A",
                "explanation": "NIC classification follows the principal activity rule, defined by the activity contributing highest gross value added.",
                "distractor_analysis": {
                    "B": "Historical sequence is irrelevant to current economic classification.",
                    "C": "Statistical officers cannot alter legal entity structures during survey enumeration.",
                    "D": "Generic coding violates standard classification protocols."
                }
            },
            # 8. CPI & Index Numbers Compilation (OSS-STAT-08)
            {
                "pool_id": "POOL-08",
                "competency_mapped": "OSS-STAT-08",
                "bloom_taxonomy_level": "Analysis",
                "scenario_text": "When compiling the Consumer Price Index (CPI), a specific item in the consumption basket (e.g. kerosene under PDS) is temporarily unavailable in a market. What is the standard imputation method?",
                "options": {
                    "A": "Impute the price movement based on the geometric mean of price relatives of closely related items in the same sub-group.",
                    "B": "Record zero price for that month.",
                    "C": "Drop the item permanently from the state CPI weighting diagram.",
                    "D": "Carry forward the price from 5 years ago without adjustment."
                },
                "correct_option": "A",
                "explanation": "Standard CPI compilation utilizes sub-group price relative trends or paired market imputation to maintain basket continuity.",
                "distractor_analysis": {
                    "B": "Entering zero price creates a false 100% deflationary drop.",
                    "C": "Weighting diagrams are fixed to the base year and cannot be altered monthly.",
                    "D": "Using multi-year outdated prices distorts inflation measurement."
                }
            },
            # 9. National Accounts & GSDP (OSS-STAT-09)
            {
                "pool_id": "POOL-09",
                "competency_mapped": "OSS-STAT-09",
                "bloom_taxonomy_level": "Evaluation",
                "scenario_text": "When compiling Gross State Domestic Product (GSDP) for the construction sector, why is the 'Double Deflation' method conceptually preferred over single deflation?",
                "options": {
                    "A": "It separately deflates gross output with an output price index and intermediate consumption with an input price index.",
                    "B": "It divides the nominal GSDP by 2 to account for unorganized workers.",
                    "C": "It converts local currency directly to US Dollars twice.",
                    "D": "It doubles the final GSDP growth rate to adjust for inflation."
                },
                "correct_option": "A",
                "explanation": "SNA 2008 recommends double deflation to accurately isolate true volume changes in value added when input and output prices diverge.",
                "distractor_analysis": {
                    "B": "Double deflation refers to price index adjustments, not dividing by 2.",
                    "C": "Currency conversion is unrelated to constant price GSDP compilation.",
                    "D": "Double deflation does not multiply growth rates."
                }
            },
            # 10. Statistical Dissemination & Visualization (OSS-STAT-10)
            {
                "pool_id": "POOL-10",
                "competency_mapped": "OSS-STAT-10",
                "bloom_taxonomy_level": "Understanding",
                "scenario_text": "When publishing district-level survey estimates on a public MoSPI portal, which accompanying metric is mandatory to prevent misuse of low-sample estimates?",
                "options": {
                    "A": "The Coefficient of Variation (CV) or Relative Standard Error (RSE) alongside sample count flags.",
                    "B": "Personal phone numbers of surveyed households.",
                    "C": "The raw unweighted interview audio recordings.",
                    "D": "A copyright watermark covering the chart."
                },
                "correct_option": "A",
                "explanation": "Official dissemination standards mandate providing RSE/CV so policymakers can assess estimation reliability before making policy decisions.",
                "distractor_analysis": {
                    "B": "Sharing respondent contact information violates statutory confidentiality.",
                    "C": "Raw audio compromises privacy and does not indicate statistical precision.",
                    "D": "Watermarking does not provide analytical reliability metrics."
                }
            },
            # 11. Survey Sampling & Circular Systematic Sampling (OSS-STAT-01)
            {
                "pool_id": "POOL-11",
                "competency_mapped": "OSS-STAT-01",
                "bloom_taxonomy_level": "Application",
                "scenario_text": "In a village with 120 listed households, 8 households must be selected using Circular Systematic Sampling with sampling interval k = 15. The random start selected is R = 9. What is the 3rd sample household?",
                "options": {
                    "A": "Household number 39",
                    "B": "Household number 24",
                    "C": "Household number 45",
                    "D": "Household number 54"
                },
                "correct_option": "A",
                "explanation": "The selected sequence is R, R+k, R+2k... For the 3rd unit: 9 + 2(15) = 9 + 30 = Household 39.",
                "distractor_analysis": {
                    "B": "24 is the 2nd sampled unit (9 + 15).",
                    "C": "45 forgets the random start offset (3 * 15).",
                    "D": "54 corresponds to the 4th sampled unit (9 + 45)."
                }
            },
            # 12. Field Scrutiny & CAPI Inconsistency (OSS-STAT-02)
            {
                "pool_id": "POOL-12",
                "competency_mapped": "OSS-STAT-02",
                "bloom_taxonomy_level": "Application",
                "scenario_text": "In Schedule 10 (Employment & Unemployment), an individual is coded as 'Attending educational institution' in Usual Principal Activity, but reported 60 hours of casual labor per week under Current Daily Status. How should the scrutiny officer proceed?",
                "options": {
                    "A": "Probe for student status vs active labor participation to reconcile activity status with reference periods.",
                    "B": "Force both codes to 'Unemployed' without asking.",
                    "C": "Delete the entire household schedule.",
                    "D": "Ignore the entry as reference periods are always independent."
                },
                "correct_option": "A",
                "explanation": "Usual Principal Activity reflects major time over 365 days whereas Current Daily Status reflects the past 7 days; probing is needed to confirm genuine student working part-time or misclassification.",
                "distractor_analysis": {
                    "B": "Arbitrarily forcing codes destroys valid economic data.",
                    "C": "Deleting schedules without verification violates survey protocols.",
                    "D": "Failing to scrutinize logical extremes introduces non-sampling errors."
                }
            },
            # 13. Data Quality Assurance - Index of Inconsistency (OSS-STAT-05)
            {
                "pool_id": "POOL-13",
                "competency_mapped": "OSS-STAT-05",
                "bloom_taxonomy_level": "Analysis",
                "scenario_text": "A supervisory re-interview of 50 sample households reveals an Index of Inconsistency (IoI) of 34% for a subjective morbidity question. What does this high IoI indicate?",
                "options": {
                    "A": "High response variability due to ambiguous question wording or inconsistent enumerator probing.",
                    "B": "The sample size was too large.",
                    "C": "Zero non-sampling error in the survey.",
                    "D": "The supervisory officer made a calculation mistake."
                },
                "correct_option": "A",
                "explanation": "An Index of Inconsistency above 20-30% indicates moderate to high response variability and unreliable question comprehension.",
                "distractor_analysis": {
                    "B": "Large sample size stabilizes variance rather than inflating inconsistency.",
                    "C": "High IoI directly proves presence of non-sampling response error.",
                    "D": "IoI is a standardized metric of survey response instability."
                }
            },
            # 14. Data Privacy - Differential Privacy & Cell Suppression (OSS-STAT-07)
            {
                "pool_id": "POOL-14",
                "competency_mapped": "OSS-STAT-07",
                "bloom_taxonomy_level": "Application",
                "scenario_text": "In a published cross-tabulation of enterprise revenue by district and 4-digit NIC code, a single cell contains only 1 dominant enterprise. How must this cell be protected?",
                "options": {
                    "A": "Apply primary and complementary cell suppression to prevent direct identification of the single unit's financials.",
                    "B": "Publish the revenue directly with the firm's PAN number.",
                    "C": "Double the cell value.",
                    "D": "Exclude the entire state from the national report."
                },
                "correct_option": "A",
                "explanation": "Statistical disclosure control mandates primary cell suppression (dominant unit) plus complementary suppression (so cell cannot be derived via row/column subtotals).",
                "distractor_analysis": {
                    "B": "Disclosing enterprise-specific financials violates statutory business confidentiality.",
                    "C": "Falsifying values corrupts the official aggregate ledger.",
                    "D": "Excluding whole states is disproportionate and unnecessary."
                }
            },
            # 15. Consumer Price Index - Geometric Mean Aggregation (OSS-STAT-08)
            {
                "pool_id": "POOL-15",
                "competency_mapped": "OSS-STAT-08",
                "bloom_taxonomy_level": "Analysis",
                "scenario_text": "Why do modern official price index guidelines recommend the Jevons elementary index (geometric mean of price relatives) over the Dutot index (ratio of arithmetic means)?",
                "options": {
                    "A": "The geometric mean satisfies the time-reversal and transitivity tests and is less sensitive to extreme price outliers.",
                    "B": "The geometric mean is always twice as large as the arithmetic mean.",
                    "C": "Arithmetic means cannot be calculated on computers.",
                    "D": "The Dutot index is illegal in India."
                },
                "correct_option": "A",
                "explanation": "The Jevons geometric formulation prevents upward substitution bias and satisfies axiomatic index number properties.",
                "distractor_analysis": {
                    "B": "The geometric mean is always less than or equal to the arithmetic mean (AM >= GM).",
                    "C": "Arithmetic means are trivially computable.",
                    "D": "Dutot is a valid statistical formula but sensitive to commodity unit definitions."
                }
            }
        ]

        # Filter out recently seen scenario IDs or scenario texts if provided
        excluded = set(excluded_scenario_hashes or [])
        available_pool = [
            q for q in full_pool 
            if q.get("pool_id") not in excluded and q.get("scenario_text", "")[:40] not in excluded
        ]

        # If available pool is too small, prioritize all unseen questions and backfill from full pool
        if len(available_pool) < num_questions:
            unseen = list(available_pool)
            seen = [q for q in full_pool if q not in unseen]
            random.shuffle(seen)
            available_pool = unseen + seen[:max(0, num_questions - len(unseen))]

        # Shuffle and sample
        random.shuffle(available_pool)
        selected = available_pool[:min(num_questions, len(available_pool))]

        # Assign clean incremental question IDs (Q1, Q2, ...)
        formatted_qs = []
        for idx, q in enumerate(selected[:num_questions]):
            q_copy = dict(q)
            q_copy["question_id"] = f"Q{idx + 1}"
            q_copy["question_type"] = q_copy.get("question_type") or "mcq"
            if not q_copy.get("question_text"):
                q_copy["question_text"] = q_copy.get("scenario_text", "")
            formatted_qs.append(q_copy)

        return formatted_qs

ai_service = AIService()
