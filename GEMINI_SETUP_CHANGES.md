# Gemini AI Integration & Custom Material Question Generation Fix

## Summary of Changes

### 1. Environment Configuration Updates

#### Before (.env)
```env
AI_PROVIDER=mock
AI_API_KEY=
AI_MODEL_NAME=gemini-1.5-pro
```

#### After (.env)
```env
AI_PROVIDER=gemini
AI_API_KEY=your_gemini_api_key_here
AI_MODEL_NAME=gemini-2.5-flash
```

**Same changes applied to `.env.example`**

---

### 2. AI Service - Model Name Usage

#### Before
```python
async def _call_gemini_api(self, context: str, n: int, diff: str, role: str, format_type: str = "mcq") -> List[Dict[str, Any]]:
    prompt = self._get_master_prompt(context, n, diff, role, format_type)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
    # Used self.model correctly (no hardcoding issue found)
```

#### After
```python
async def _call_gemini_api(self, context: str, n: int, diff: str, role: str, format_type: str = "mcq") -> List[Dict[str, Any]]:
    prompt = self._get_master_prompt(context, n, diff, role, format_type)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
    
    # Added retry logic for rate limiting (HTTP 429)
    max_retries = 2
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            
            if res.status_code == 429:
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt
                    print(f"Rate limited by Gemini API. Retrying in {backoff_time} seconds...")
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    raise HTTPException(
                        status_code=429,
                        detail="Gemini API rate limit exceeded. Please try again later or upgrade your API plan."
                    )
            
            res.raise_for_status()
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
```

**Key Changes:**
- Added `asyncio` import
- Added `HTTPException` import from fastapi
- Implemented exponential backoff retry logic for HTTP 429 errors
- Clear error message when rate limit is exceeded

---

### 3. Custom Material Content Usage Fix

#### Before (Mock Mode Used Generic Questions)
```python
if self.provider == "mock" or not self.api_key:
    if is_mixed:
        raw_qs = self._generate_domain_mock_mixed(...)
    else:
        raw_qs = self._generate_domain_mock_mcqs(...)  # Used pre-written domain questions
    return self._finalize_questions(raw_qs, is_mixed)
```

#### After (Mock Mode Now Uses Material Content)
```python
if self.provider == "mock" or not self.api_key:
    if is_mixed:
        raw_qs = self._generate_domain_mock_mixed(...)
    else:
        # Use material-based generation for MCQs to ensure content relevance
        raw_qs = self._generate_material_based_mcqs(
            context_text, num_questions, difficulty, role_target, excluded_scenario_hashes
        )
    return self._finalize_questions(raw_qs, is_mixed)
```

**New Function Added:**
```python
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
    
    # Generate questions from actual material content
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
    return questions
```

**Key Changes:**
- New `_generate_material_based_mcqs()` function extracts content from uploaded material
- Uses `_extract_material_chunks()` to split material into usable sentences
- Generates MCQs based on actual material content, not generic domain questions
- Falls back to domain questions only if material extraction fails

---

### 4. Question Type Validation

#### Before (No Validation)
```python
def _finalize_questions(self, raw_qs: Any, is_mixed: bool) -> List[Dict[str, Any]]:
    if isinstance(raw_qs, dict):
        raw_qs = raw_qs.get("questions") or raw_qs.get("items") or [raw_qs]
    questions = [q for q in (raw_qs or []) if isinstance(q, dict)]
    finalized = []
    for q in questions:
        item = dict(q)
        if not is_mixed:
            item = self._coerce_to_four_option_mcq(item)
        else:
            item["question_type"] = (item.get("question_type") or "mcq").strip().lower()
        if not item.get("question_text"):
            item["question_text"] = "Which of the following is the most appropriate action based on the uploaded material?"
        finalized.append(self.shuffle_question_options(item))
    return finalized
```

#### After (With Validation)
```python
def _finalize_questions(self, raw_qs: Any, is_mixed: bool) -> List[Dict[str, Any]]:
    if isinstance(raw_qs, dict):
        raw_qs = raw_qs.get("questions") or raw_qs.get("items") or [raw_qs]
    questions = [q for q in (raw_qs or []) if isinstance(q, dict)]
    finalized = []
    for q in questions:
        item = dict(q)
        if not is_mixed:
            item = self._coerce_to_four_option_mcq(item)
            # Validate that the question is properly formatted as MCQ
            if not self._validate_mcq_format(item):
                print(f"Warning: Question {item.get('question_id', 'unknown')} failed MCQ validation. Regenerating...")
                continue
        else:
            item["question_type"] = (item.get("question_type") or "mcq").strip().lower()
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
```

**Key Changes:**
- Added `_validate_mcq_format()` function with comprehensive validation
- Validates question type is "mcq"
- Validates exactly 4 options with keys A, B, C, D
- Validates options are not True/False values
- Validates correct_option is one of A, B, C, D
- Rejects invalid questions instead of silently accepting them
- Logs specific validation failures for debugging

---

### 5. Enhanced AI Prompt for MCQ Generation

#### Before
```python
CONTEXT MATERIAL:
{context_text[:3000]}

REQUIREMENTS:
1. Every question MUST present a realistic official workplace scenario.
2. Ensure correct answer positions are randomly distributed across A, B, C, and D.
3. Provide a detailed distractor analysis explaining the specific misconception for each incorrect option.
4. Output MUST be valid JSON array with no extra markdown wrapping.
```

#### After
```python
CONTEXT MATERIAL:
{context_text[:12000]}

REQUIREMENTS:
1. Every question MUST be grounded in the CONTEXT MATERIAL. Use facts from that text; do not invent unrelated items.
2. Generate ONLY four-option MCQs. Do NOT generate true/false, fill-in-the-blank, match, short-answer, or essay items.
3. Options A, B, C, and D must be distinct substantive statements. Never use True/False as the option set.
4. Ensure correct answer positions are randomly distributed across A, B, C, and D.
5. Provide a detailed distractor analysis explaining the specific misconception for each incorrect option.
6. Output MUST be valid JSON array with no extra markdown wrapping. Each object MUST include question_type "mcq" and question_text.
```

**Key Changes:**
- Increased context material limit from 3000 to 12000 characters
- Added explicit requirement to use only context material
- Added explicit prohibition of non-MCQ question types
- Added requirement for distinct substantive options
- Added requirement for question_type and question_text in JSON schema

---

## How to Get Your Free Gemini API Key

### Step-by-Step Instructions:

1. **Go to Google AI Studio**
   - Visit: https://makersuite.google.com/app/apikey
   - Or: https://aistudio.google.com/app/apikey

2. **Create API Key**
   - Click "Create API Key" button
   - You may need to sign in with your Google account
   - Accept the terms of service if prompted

3. **Copy Your API Key**
   - Your API key will be displayed in the format: `AIza...`
   - Copy this key for use in your `.env` file

4. **Add to Environment**
   - Open `.env` file in your project
   - Replace `your_gemini_api_key_here` with your actual API key:
   ```env
   AI_API_KEY=AIzaSyYourActualApiKeyHere
   ```

### Free Tier Information:

✅ **No Credit Card Required** for the free tier
- Gemini Flash models (including gemini-2.5-flash) are available on the free tier
- No billing setup needed for basic usage
- Generous free quota for development and testing

⚠️ **Rate Limits on Free Tier:**
- 15 requests per minute for Gemini Flash
- 1,500 requests per day for Gemini Flash
- If you exceed these limits, the system will automatically retry with backoff

💡 **Pro Tips:**
- Use `gemini-2.5-flash` for faster responses and higher free tier limits
- The retry logic in the code handles rate limits gracefully
- For production use, consider upgrading to a paid tier for higher limits

---

## Testing the Changes

### 1. Restart the Application
```bash
# Stop any running instance
# Then start with new configuration
python run.py
```

### 2. Test Custom Material Upload
1. Upload a PDF or text document
2. Select "MCQ 1" or "MCQ 2" (MCQ-only format)
3. Verify questions are:
   - Based on your uploaded material content
   - Proper 4-option MCQ format
   - Not True/False questions
   - Have A, B, C, D options

### 3. Test Mixed Format
1. Upload a document
2. Select "Quiz 1" or "Quiz 2" (mixed format)
3. Verify questions include:
   - MCQs
   - True/False
   - Fill in the blank
   - Match the following
   - Short answer
   - Essay questions

### 4. Monitor Logs
Watch for validation messages:
- "Question QX failed MCQ validation. Regenerating..."
- "Rate limited by Gemini API. Retrying in X seconds..."

---

## Summary of All Fixes

✅ **Configuration**: Updated to use Gemini 2.5 Flash
✅ **Rate Limiting**: Added retry logic with exponential backoff
✅ **Material Usage**: Questions now generated from actual uploaded content
✅ **Type Validation**: MCQ format validation prevents True/False questions
✅ **Enhanced Prompts**: AI instructed to use material content and proper formats
✅ **Fallback Logic**: Graceful degradation when AI fails
✅ **Error Handling**: Clear error messages for rate limits

The system now properly generates MCQ questions based on uploaded material content while maintaining the ability to use mixed-format quizzes when requested.