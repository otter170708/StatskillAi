# API Documentation

## Base URL
```
Development: http://localhost:8000
Production: https://api.statskill.gov.in
```

## Authentication
Currently using development mode. Production will integrate with government SSO.

## Response Format
All responses follow standard JSON format:
```json
{
  "data": { ... },
  "message": "Success message",
  "status": "success"
}
```

## Error Responses
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

## Core Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "app_name": "StatSkill AI",
  "environment": "development",
  "ai_provider": "gemini",
  "ocr_enabled": true
}
```

---

## Materials API

### Upload Material
```http
POST /api/materials/upload
Content-Type: multipart/form-data
```

**Request Body:**
- `file`: PDF or text file (max 15MB)
- `title`: Material title (string)
- `source_type`: Source type (pdf, text, circular)
- `language`: Language code (default: English)

**Response:**
```json
{
  "material_id": "MAT-001",
  "title": "NSSO 79th Round Guidelines",
  "source_type": "pdf",
  "language": "English",
  "extracted_text": "...",
  "topic_tags": ["survey", "methodology", "field operations"],
  "created_at": "2026-09-15T10:30:00Z"
}
```

### List Materials
```http
GET /api/materials
```

**Query Parameters:**
- `source_type`: Filter by source type (optional)
- `language`: Filter by language (optional)

**Response:**
```json
[
  {
    "material_id": "MAT-001",
    "title": "NSSO 79th Round Guidelines",
    "source_type": "pdf",
    "language": "English",
    "created_at": "2026-09-15T10:30:00Z"
  }
]
```

### Get Material
```http
GET /api/materials/{material_id}
```

**Response:**
```json
{
  "material_id": "MAT-001",
  "title": "NSSO 79th Round Guidelines",
  "source_type": "pdf",
  "language": "English",
  "extracted_text": "Full text content...",
  "topic_tags": ["survey", "methodology"],
  "created_at": "2026-09-15T10:30:00Z"
}
```

---

## Quizzes API

### Generate Quiz
```http
POST /api/quizzes/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "material_id": "MAT-001",
  "num_questions": 5,
  "difficulty": "medium",
  "role_target": "Junior Statistical Officer",
  "format_type": "mcq"
}
```

**Parameters:**
- `material_id`: Source material ID
- `num_questions`: Number of questions (1-20)
- `difficulty`: easy, medium, hard
- `role_target`: Target role for scenario context
- `format_type`: mcq, true_false, mixed

**Response:**
```json
{
  "quiz_id": "QUIZ-001",
  "material_id": "MAT-001",
  "title": "NSSO 79th Round Assessment",
  "num_questions": 5,
  "difficulty": "medium",
  "status": "ready",
  "created_at": "2026-09-15T10:35:00Z",
  "questions": [
    {
      "question_id": "Q1",
      "question_type": "mcq",
      "competency_mapped": "OSS-STAT-02",
      "bloom_taxonomy_level": "Application",
      "scenario_text": "You are conducting a household survey...",
      "question_text": "Which action is most appropriate?",
      "options": {
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      },
      "correct_option": "A",
      "explanation": "Detailed explanation...",
      "distractor_analysis": {
        "B": "Why B is incorrect",
        "C": "Why C is incorrect",
        "D": "Why D is incorrect"
      }
    }
  ]
}
```

### Submit Quiz Attempt
```http
POST /api/quizzes/{quiz_id}/attempt
Content-Type: application/json
```

**Request Body:**
```json
{
  "learner_id": "LRN-001",
  "answers": [
    {
      "question_id": "Q1",
      "selected_option": "A",
      "confidence": "high"
    }
  ]
}
```

**Parameters:**
- `learner_id`: Learner identifier
- `answers`: Array of answer submissions
  - `question_id`: Question identifier
  - `selected_option`: Selected option (A, B, C, D)
  - `confidence`: low, medium, high

**Response:**
```json
{
  "attempt_id": "ATT-001",
  "quiz_id": "QUIZ-001",
  "learner_id": "LRN-001",
  "score": 4,
  "total_questions": 5,
  "percentage": 80.0,
  "grade_message": "Good performance. Target specific procedural gaps identified below.",
  "competency_scores": [
    {
      "competency_id": "OSS-STAT-02",
      "competency_name": "Field Scrutiny & Schedule Validation",
      "correct": 3,
      "total": 4,
      "percentage": 75.0,
      "status": "Proficient"
    }
  ],
  "diagnosed_gaps": [
    {
      "competency_id": "OSS-STAT-03",
      "competency_name": "Outlier Detection & Imputation Techniques",
      "gap_nature": "Functional",
      "severity": "High",
      "diagnostic_summary": "Low accuracy in outlier detection protocols.",
      "recommended_focus_area": "Practical field rules & case studies for Outlier Detection",
      "confidence_factor": "High Misconception"
    }
  ],
  "recommended_courses": [
    {
      "course_id": "NSSTA-103",
      "course_title": "Advanced Outlier Detection Methods",
      "provider": "NSSTA / MoSPI",
      "duration_minutes": 90,
      "target_gap_addressed": "OSS-STAT-03",
      "justification": "Directly addresses identified gap in outlier detection techniques"
    }
  ],
  "question_reviews": [
    {
      "question_id": "Q1",
      "competency_mapped": "OSS-STAT-02",
      "scenario_text": "Scenario text...",
      "options": {...},
      "selected_option": "A",
      "correct_option": "A",
      "is_correct": true,
      "confidence": "high",
      "explanation": "Explanation...",
      "distractor_feedback": ""
    }
  ],
  "completed_at": "2026-09-15T10:40:00Z"
}
```

### List Quizzes
```http
GET /api/quizzes
```

**Query Parameters:**
- `material_id`: Filter by material (optional)
- `difficulty`: Filter by difficulty (optional)
- `status`: Filter by status (optional)

**Response:**
```json
[
  {
    "quiz_id": "QUIZ-001",
    "material_id": "MAT-001",
    "title": "NSSO 79th Round Assessment",
    "num_questions": 5,
    "difficulty": "medium",
    "status": "ready",
    "created_at": "2026-09-15T10:35:00Z"
  }
]
```

---

## Learners API

### List Learners
```http
GET /api/learners
```

**Response:**
```json
[
  {
    "learner_id": "LRN-001",
    "name": "Rajesh Kumar",
    "role": "Junior Statistical Officer",
    "department": "NSSO Regional Office",
    "experience_level": "intermediate",
    "preferred_language": "English",
    "karma_points": 350,
    "streak_days": 7,
    "total_quizzes": 12
  }
]
```

### Get Learner Dashboard
```http
GET /api/learners/{learner_id}/dashboard
```

**Response:**
```json
{
  "learner": {
    "learner_id": "LRN-001",
    "name": "Rajesh Kumar",
    "role": "Junior Statistical Officer",
    "department": "NSSO Regional Office",
    "experience_level": "intermediate",
    "preferred_language": "English",
    "karma_points": 350,
    "streak_days": 7,
    "total_quizzes": 12
  },
  "total_quizzes_taken": 12,
  "average_score": 78.5,
  "learning_streak_days": 7,
  "karma_points_earned": 350,
  "active_competency_gaps": [
    {
      "competency_id": "OSS-STAT-03",
      "competency_name": "Outlier Detection & Imputation Techniques",
      "gap_nature": "Functional",
      "severity": "High",
      "diagnostic_summary": "Low accuracy in outlier detection protocols."
    }
  ],
  "recent_attempts": [
    {
      "attempt_id": "ATT-001",
      "quiz_id": "QUIZ-001",
      "score": 4,
      "total": 5,
      "percentage": 80.0,
      "completed_at": "2026-09-15T10:40:00Z"
    }
  ],
  "recommended_courses": [
    {
      "course_id": "NSSTA-103",
      "course_title": "Advanced Outlier Detection Methods",
      "provider": "NSSTA / MoSPI",
      "duration_minutes": 90,
      "target_gap_addressed": "OSS-STAT-03"
    }
  ],
  "competency_mastery_radar": [
    {
      "competency_id": "OSS-STAT-01",
      "competency_name": "Survey Methodology & Sampling Frame Design",
      "score": 85,
      "domain": "Knowledge"
    }
  ]
}
```

### Get Official Dossier
```http
GET /api/learners/{learner_id}/dossier
```

**Response:**
```json
{
  "dossier_id": "MOSPI-APAR-2026-LRN001",
  "issued_at": "15 September 2026, 10:45 UTC",
  "issuing_authority": "National Statistical Systems Training Academy (NSSTA), MoSPI, Govt. of India",
  "officer": {
    "name": "Rajesh Kumar",
    "learner_id": "LRN-001",
    "role": "Junior Statistical Officer",
    "cadre": "Subordinate Statistical Service (SSS) / Indian Statistical Service (ISS)",
    "department": "NSSO Regional Office",
    "station": "Regional Office, Field Operations Division (NSSO)",
    "experience_level": "intermediate",
    "preferred_language": "English"
  },
  "assessment_summary": {
    "assessments_completed": 12,
    "average_mastery_percentage": 78.5,
    "cumulative_karma_points": 350,
    "competency_tier": "Tier-2 Operational Practitioner",
    "apar_impact_rating": "Positive - Continuous Capacity Building Compliance"
  },
  "competency_breakdown": [
    {
      "code": "OSS-STAT-01",
      "name": "Survey Methodology & Sampling Frame",
      "score": 82,
      "status": "PROFICIENT"
    }
  ],
  "critical_misconceptions": [
    {
      "competency_id": "OSS-STAT-03",
      "competency_name": "Outlier Detection & Imputation Techniques",
      "severity": "Critical",
      "diagnostic_summary": "High-confidence misclassification of missing consumption data without physical re-inspection."
    }
  ],
  "mandated_igot_courses": [
    {
      "course_id": "NSSTA-103",
      "course_title": "Advanced Outlier Detection Methods",
      "provider": "NSSTA / MoSPI",
      "duration_minutes": 90,
      "target_gap_addressed": "OSS-STAT-03",
      "justification": "Directly rectifies improper schedule imputation and re-inspection protocols."
    }
  ],
  "digital_seal_hash": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",
  "apar_compliance_status": "CERTIFIED_AUDIT_READY"
}
```

---

## Courses API

### List Courses
```http
GET /api/courses
```

**Query Parameters:**
- `competency_id`: Filter by competency (optional)

**Response:**
```json
[
  {
    "course_id": "NSSTA-101",
    "course_name": "Survey Methodology Fundamentals",
    "description": "Comprehensive introduction to survey design and sampling techniques",
    "competency_ids": ["OSS-STAT-01", "OSS-STAT-02"],
    "level": "basic",
    "language": "English",
    "duration_minutes": 60,
    "provider": "NSSTA / MoSPI",
    "course_url": "https://igotkarmayogi.gov.in/course/101",
    "igot_course_id": "IGOT-101"
  }
]
```

### Enroll in Course
```http
POST /api/courses/{course_id}/enrol
Content-Type: application/json
```

**Request Body:**
```json
{
  "learner_id": "LRN-001",
  "competency_id": "OSS-STAT-01"
}
```

**Response:**
```json
{
  "status": "SUCCESS",
  "enrolment_id": "IGOT-ENR-A1B2C3D4",
  "course_id": "NSSTA-101",
  "course_name": "Survey Methodology Fundamentals",
  "learner_id": "LRN-001",
  "learner_name": "Rajesh Kumar",
  "igot_sync_status": "SYNCED_TO_APAR_LEDGER",
  "apar_competency_linked": "OSS-STAT-01",
  "karma_credit_awarded": 25,
  "message": "Official Rajesh Kumar successfully enrolled in 'Survey Methodology Fundamentals'. MoSPI APAR Competency Ledger synced.",
  "enrolled_at": "2026-09-15 10:50:00 UTC"
}
```

---

## Competencies API

### List Competencies
```http
GET /api/competencies
```

**Response:**
```json
[
  {
    "competency_id": "OSS-STAT-01",
    "competency_name": "Survey Methodology & Sampling Frame Design",
    "description": "Understanding of survey design principles, sampling techniques, and frame construction",
    "level": "intermediate",
    "domain": "Knowledge"
  }
]
```

### Get Competency
```http
GET /api/competencies/{competency_id}
```

**Response:**
```json
{
  "competency_id": "OSS-STAT-01",
  "competency_name": "Survey Methodology & Sampling Frame Design",
  "description": "Understanding of survey design principles, sampling techniques, and frame construction",
  "level": "intermediate",
  "domain": "Knowledge"
}
```

---

## SME Review API

### Submit for Review
```http
POST /api/sme-review/submit
Content-Type: application/json
```

**Request Body:**
```json
{
  "quiz_id": "QUIZ-001",
  "reviewer_id": "SME-001",
  "notes": "Questions look accurate and aligned with competencies"
}
```

**Response:**
```json
{
  "status": "submitted",
  "quiz_id": "QUIZ-001",
  "reviewer_id": "SME-001",
  "submitted_at": "2026-09-15T11:00:00Z"
}
```

### Approve Question
```http
POST /api/sme-review/questions/{question_id}/approve
Content-Type: application/json
```

**Request Body:**
```json
{
  "reviewer_id": "SME-001",
  "notes": "Question approved with minor clarification"
}
```

**Response:**
```json
{
  "status": "approved",
  "question_id": "Q1",
  "reviewer_id": "SME-001",
  "reviewed_at": "2026-09-15T11:05:00Z"
}
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

---

## Rate Limiting

- **Gemini API**: 15 requests/minute, 1,500 requests/day (free tier)
- **General API**: No rate limiting in development
- **Production**: TBD based on infrastructure

---

## Interactive Documentation

Interactive API documentation available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

---

## Data Models

### Competency
```typescript
{
  competency_id: string;
  competency_name: string;
  description: string;
  level: "basic" | "intermediate" | "advanced";
  domain: "Knowledge" | "Functional" | "Behavioral/Compliance";
}
```

### Course
```typescript
{
  course_id: string;
  course_name: string;
  description: string;
  competency_ids: string[];
  level: "basic" | "intermediate" | "advanced";
  language: string;
  duration_minutes: number;
  provider: string;
  course_url?: string;
  igot_course_id?: string;
}
```

### Learner
```typescript
{
  learner_id: string;
  name: string;
  role: string;
  department: string;
  experience_level: "basic" | "intermediate" | "advanced";
  preferred_language: string;
  karma_points: number;
  streak_days: number;
  total_quizzes: number;
}
```

### Quiz
```typescript
{
  quiz_id: string;
  material_id?: string;
  title: string;
  num_questions: number;
  difficulty: "easy" | "medium" | "hard";
  status: "ready" | "in_review" | "archived";
  created_at: string;
  questions: Question[];
}
```

### Question
```typescript
{
  question_id: string;
  question_type: "mcq" | "true_false" | "fill_blank" | "match" | "short_answer" | "essay";
  competency_mapped: string;
  bloom_taxonomy_level: "Recall" | "Understanding" | "Application" | "Analysis";
  scenario_text: string;
  question_text: string;
  options?: { [key: string]: string };
  correct_option: string;
  explanation: string;
  distractor_analysis?: { [key: string]: string };
  review_status: "APPROVED" | "PENDING" | "NEEDS_REVISION";
  reviewer_notes?: string;
}
```

---

## WebSocket Events (Planned)

### Real-time Updates
```javascript
// Quiz completion notification
{
  event: "quiz_completed",
  data: {
    learner_id: "LRN-001",
    quiz_id: "QUIZ-001",
    score: 80,
    timestamp: "2026-09-15T10:40:00Z"
  }
}

// Course enrollment notification
{
  event: "course_enrolled",
  data: {
    learner_id: "LRN-001",
    course_id: "NSSTA-101",
    enrollment_id: "IGOT-ENR-A1B2C3D4"
  }
}
```

---

## Testing API Endpoints

### Using cURL
```bash
# Health check
curl http://localhost:8000/api/health

# Upload material
curl -X POST http://localhost:8000/api/materials/upload \
  -F "file=@document.pdf" \
  -F "title=Test Document" \
  -F "source_type=pdf"

# Generate quiz
curl -X POST http://localhost:8000/api/quizzes/generate \
  -H "Content-Type: application/json" \
  -d '{"material_id":"MAT-001","num_questions":5,"difficulty":"medium"}'
```

### Using Python
```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# Generate quiz
payload = {
    "material_id": "MAT-001",
    "num_questions": 5,
    "difficulty": "medium"
}
response = requests.post(
    "http://localhost:8000/api/quizzes/generate",
    json=payload
)
print(response.json())
```

---

For more details, refer to the interactive API documentation at `/docs` or the architecture documentation in `ARCHITECTURE.md`.