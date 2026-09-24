# Technical Architecture

## System Overview

StatSkill AI follows a modern microservices-inspired architecture with clear separation of concerns, designed for scalability, maintainability, and performance. The system is built using FastAPI for the backend with a reactive frontend, ensuring real-time responsiveness and excellent developer experience.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Alpine.js  │  │  Tailwind CSS│  │   Chart.js   │          │
│  │  (Reactive)  │  │  (Styling)   │  │ (Visualization)│         │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│                    FastAPI Application                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  CORS & Auth │  │  Validation  │  │  Error Hdlr  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Business Lyr │    │   AI Engine  │    │ Data Layer   │
│  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │
│  │ Routers│  │    │  │ Gemini │  │    │  │SQLAlchemy│ │
│  │Services│  │    │  │  API   │  │    │  │  ORM    │ │
│  │Schemas │  │    │  │ Fallback│  │    │  │SQLite/PG│ │
│  └────────┘  │    │  └────────┘  │    │  └────────┘  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Component Architecture

### 1. Frontend Layer

**Technology Stack:**
- **Alpine.js**: Lightweight reactive framework for state management
- **Tailwind CSS**: Utility-first CSS for responsive design
- **Chart.js**: Data visualization for competency radar and analytics
- **Lucide Icons**: Modern icon library
- **IBM Plex Fonts**: Professional typography for government applications

**Key Features:**
- Real-time reactive UI updates
- Responsive design for mobile and desktop
- Client-side form validation
- Interactive charts and dashboards
- Accessibility-first design

### 2. API Gateway (FastAPI)

**Core Responsibilities:**
- Request routing and validation
- CORS configuration
- Error handling and logging
- API documentation (OpenAPI/Swagger)
- Static file serving

**Middleware Stack:**
```python
CORSMiddleware (allow_origins=["*"])
├── Request Validation (Pydantic schemas)
├── Error Handling (HTTPException)
├── Logging (custom log levels)
└── Response Formatting (JSON)
```

### 3. Business Logic Layer

#### Router Modules
- `materials.py`: Document upload and processing
- `quizzes.py`: Quiz generation and attempt management
- `learners.py`: Learner profiles and dashboards
- `courses.py`: iGOT course catalog and enrollment
- `competencies.py`: Competency framework management
- `sme_review.py`: SME review workflow

#### Service Modules
- `ai_service.py`: AI-powered question generation
- `diagnostic_engine.py`: Competency gap analysis
- `document_service.py`: PDF/text processing
- `recsys_service.py`: Course recommendation algorithm
- `seed_service.py`: Database initialization

### 4. AI Engine

**Gemini Integration:**
```python
AIService Class
├── generate_mcqs() - Main generation orchestrator
├── _call_gemini_api() - Gemini API integration
├── _generate_local_fallback() - Offline fallback
├── _validate_mcq_format() - Question validation
└── shuffle_question_options() - Randomization
```

**Key Features:**
- Structured JSON output enforcement
- Rate limiting with exponential backoff
- Material-based content extraction
- Multi-format question generation (MCQ, True/False, etc.)
- Bloom's taxonomy alignment

**Fallback Strategy:**
```
Primary: Gemini 2.5 Flash API
├── Success: Return AI-generated questions
└── Failure: Local material-based generation
    ├── Extract chunks from uploaded material
    ├── Generate MCQs from content
    └── Fallback to domain-specific questions
```

### 5. Data Layer

**Database Schema:**
```python
Core Models:
├── Competency (10 statistical domains)
├── Course (iGOT course catalog)
├── Learner (civil servant profiles)
├── Material (training documents)
├── Quiz (generated assessments)
├── Question (individual questions)
└── Attempt (learner quiz attempts)
```

**Database Design:**
- **Development**: SQLite (file-based, zero configuration)
- **Production**: PostgreSQL (scalable, ACID compliant)
- **ORM**: SQLAlchemy with async support
- **Migrations**: Manual schema upgrade functions

**Relationships:**
```
Learner (1) ─────── (N) Attempt
Quiz (1) ────────── (N) Question
Quiz (1) ────────── (N) Attempt
Material (1) ────── (N) Quiz
Competency (1) ──── (N) Question
Competency (1) ──── (N) Course
```

## Data Flow

### 1. Material Upload & Quiz Generation
```
User Uploads PDF
    ↓
Document Service (PyPDF extraction)
    ↓
AI Service (Material chunking)
    ↓
Gemini API (Question generation)
    ↓
Validation & Formatting
    ↓
Database Storage (Quiz & Questions)
```

### 2. Quiz Attempt & Diagnosis
```
User Submits Answers
    ↓
Diagnostic Engine (Answer evaluation)
    ↓
Competency Analysis (Gap detection)
    ↓
Confidence Scoring (Misconception identification)
    ↓
Recommendation Service (Course matching)
    ↓
Dashboard Update (Real-time analytics)
```

### 3. Course Enrollment
```
User Selects Course
    ↓
Course Service (iGOT integration)
    ↓
Enrollment Token Generation
    ↓
APAR Ledger Sync (Compliance tracking)
    ↓
Karma Points Award (Gamification)
```

## Security Architecture

### API Security
- **CORS Configuration**: Configurable origin whitelist
- **Input Validation**: Pydantic schema validation
- **SQL Injection Prevention**: ORM parameterized queries
- **Rate Limiting**: API-level rate limiting (Gemini)
- **Error Handling**: Generic error messages (no sensitive data exposure)

### Data Security
- **API Key Management**: Environment variable storage
- **File Upload Validation**: Size limits (15MB), type restrictions
- **Session Management**: Stateless API design
- **Password Security**: Not applicable (government SSO integration planned)

## Performance Optimization

### Caching Strategy
- **Database Query Optimization**: Indexed primary keys
- **Static Asset Caching**: Browser caching for frontend assets
- **API Response Caching**: Planned Redis integration

### Database Optimization
- **Connection Pooling**: SQLAlchemy connection management
- **Query Optimization**: Selective field loading
- **Indexing Strategy**: Primary keys and foreign keys indexed

### AI Performance
- **Async Processing**: Non-blocking AI API calls
- **Rate Limit Handling**: Exponential backoff retry
- **Fallback Mechanism**: Local generation for reliability

## Scalability Considerations

### Horizontal Scaling
- **Stateless API Design**: Easy horizontal scaling
- **Database Connection Pooling**: Handles concurrent connections
- **Load Balancing Ready**: Can be deployed behind load balancers

### Vertical Scaling
- **Async Processing**: Efficient resource utilization
- **Memory Management**: Streaming for large file processing
- **CPU Optimization**: Efficient algorithms for diagnostic engine

## Monitoring & Observability

### Logging
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Error Tracking**: Comprehensive error logging

### Health Checks
- **API Health Endpoint**: `/api/health`
- **Database Connectivity**: Connection validation
- **AI Service Status**: API availability check

### Metrics (Planned)
- **Response Times**: API endpoint performance
- **Error Rates**: Failure tracking
- **User Engagement**: Quiz completion rates
- **AI Performance**: Generation success rates

## Development Workflow

### Local Development
```bash
# Environment Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database Initialization
python run.py  # Auto-creates SQLite DB

# Development Server
python run.py  # Hot reload enabled
```

### Code Organization
```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── static/              # Frontend assets
│   └── seed/                # Sample data
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── .env                     # Environment variables
```

## Deployment Architecture

### Container Strategy
```dockerfile
# Multi-stage build
Stage 1: Dependencies
Stage 2: Application
Stage 3: Production optimization
```

### Environment Configuration
- **Development**: SQLite, mock AI, debug logging
- **Staging**: PostgreSQL, Gemini API, info logging
- **Production**: PostgreSQL, Gemini API, error logging

### Infrastructure Recommendations
- **Application Server**: Gunicorn with Uvicorn workers
- **Web Server**: Nginx (reverse proxy, static files)
- **Database**: PostgreSQL (managed service recommended)
- **File Storage**: S3 or equivalent for document storage
- **Monitoring**: Prometheus + Grafana

## Technology Rationale

### Why FastAPI?
- Modern async framework with excellent performance
- Automatic API documentation (OpenAPI/Swagger)
- Type hints and Pydantic validation
- Growing ecosystem and community support

### Why Alpine.js?
- Lightweight (<15KB) compared to React/Vue
- Simple learning curve for rapid development
- Perfect for single-page applications
- No build step required

### Why Gemini 2.5 Flash?
- Fast response times for real-time generation
- Strong free tier for development
- Structured output support
- Good understanding of technical content

### Why SQLite for Development?
- Zero configuration required
- Single file database
- Easy version control
- Sufficient for development/testing

## Future Architecture Enhancements

### Planned Improvements
1. **Redis Caching**: For API responses and session data
2. **Message Queue**: For async background tasks
3. **Microservices**: Split AI engine into separate service
4. **CDN Integration**: For static asset delivery
5. **Advanced Analytics**: Separate analytics service

### Scalability Roadmap
1. **Phase 1**: Vertical scaling, database optimization
2. **Phase 2**: Horizontal scaling, load balancing
3. **Phase 3**: Microservices architecture
4. **Phase 4**: Multi-region deployment

---

This architecture provides a solid foundation for the StatSkill AI platform, balancing performance, scalability, and maintainability while keeping development velocity high.