# StatSkill AI

**AI-Enabled Learning & Assessment Platform for India's Official Statistical System**

An intelligent competency assessment and personalized learning platform designed for civil servants in the Indian statistical system, seamlessly integrated with iGOT Karmayogi platform. StatSkill AI leverages advanced AI to transform training materials into interactive assessments, diagnose skill gaps, and recommend targeted courses for continuous professional development.

## 🎯 Problem Statement

India's Official Statistical System (MoSPI/NSSO) faces critical challenges in capacity building:

- **Inconsistent Assessment Standards**: Manual evaluation lacks standardization across field offices
- **Skill Gap Blind Spots**: Traditional training fails to identify specific competency deficiencies
- **Generic Learning Paths**: One-size-fits-all courses don't address individual needs
- **APAR Compliance Burden**: Manual tracking of Annual Performance Assessment Report competencies
- **Content Stagnation**: Training materials become outdated without systematic refresh mechanisms

## 💡 Solution Overview

StatSkill AI provides an end-to-end AI-powered platform that:

1. **Transforms Training Materials** → Converts official documents, circulars, and manuals into interactive assessments
2. **Diagnoses Competency Gaps** → AI-powered analysis identifies specific skill deficiencies with confidence scoring
3. **Recommends Targeted Learning** → Maps gaps to relevant iGOT Karmayogi courses for personalized upskilling
4. **Tracks Professional Growth** → Gamified dashboards with karma points, learning streaks, and competency mastery radar
5. **Ensures APAR Compliance** → Generates official dossiers with digital seals for performance assessment

## 🚀 Key Features

### 🤖 AI-Powered Assessment Generation
- **Material Processing**: Upload PDF/text documents → AI extracts key concepts and generates scenario-based questions
- **Multi-Format Support**: MCQs, True/False, Fill-in-the-blank, Match the following, Short answer, Essay questions
- **Bloom's Taxonomy Alignment**: Questions mapped to Application, Analysis, and higher-order thinking levels
- **Competency Mapping**: Questions tagged to 10 core statistical competencies (OSS-STAT-01 to OSS-STAT-10)

### 🎯 Precision Diagnostic Engine
- **Confidence-Based Analysis**: Learners rate answer confidence → identifies high-confidence misconceptions
- **Distractor Intelligence**: Detailed analysis of why incorrect options are wrong
- **Gap Severity Scoring**: Critical, High, Medium severity classification for prioritized remediation
- **Competency Breakdown**: Performance radar across 10 statistical domains

### 📚 Intelligent Course Recommendations
- **iGOT Karmayogi Integration**: Direct mapping to official training courses
- **Gap-Based Matching**: Recommendations based on diagnosed competency deficiencies
- **APAR Compliance**: Courses linked to Annual Performance Assessment Report competencies
- **Enrollment Automation**: One-click enrollment with MoSPI APAR Competency Ledger sync

### 📊 Learner Dashboard & Gamification
- **Karma Points System**: Earn points for quiz completion (50 base + percentage × 0.5)
- **Learning Streaks**: Track consecutive days of learning engagement
- **Competency Mastery Radar**: Visual representation of skill development across domains
- **Performance Analytics**: Historical attempt tracking with detailed question-wise analysis

### 🏛️ Official Dossier Generation
- **APAR-Ready Reports**: Generates performance dossiers compliant with government standards
- **Digital Seal Authentication**: SHA-256 hashed seals for document integrity
- **Competency Tier Classification**: Tier-1, Tier-2, Tier-3 operational practitioner levels
- **Mandated Course Tracking**: Required training compliance monitoring

### 👥 SME Review Workflow
- **Quality Assurance**: Subject Matter Expert review for AI-generated questions
- **Review Status Tracking**: APPROVED, PENDING, NEEDS_REVISION workflow
- **Reviewer Notes**: Collaborative feedback mechanism for question refinement

## 🏗️ Technical Architecture

### Backend Stack
- **Framework**: FastAPI (high-performance async web framework)
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy with async support
- **AI Engine**: Google Gemini Flash (`gemini-flash-latest` via Google AI Studio API) with instant local domain fast-fallback
- **Document Processing**: PyPDF for PDF text extraction, OCR for images
- **API Documentation**: Auto-generated OpenAPI/Swagger docs (`/docs`)

### Frontend Stack
- **Framework**: Alpine.js (lightweight reactive framework)
- **Styling**: Tailwind CSS (utility-first CSS framework)
- **Charts**: Chart.js (FRAC Competency Radar & Analytics)
- **Icons**: Lucide Icons
- **Fonts**: IBM Plex Sans & Mono (official government aesthetic)

### Database Schema
- **Competencies**: 10 core statistical domains with difficulty levels
- **Courses**: iGOT Karmayogi course catalog with competency mappings
- **Learners**: Civil servant profiles with roles and departments
- **Materials**: Training documents with deduplicated titles and topic tags
- **Quizzes**: Generated assessments with questions mapped to competencies
- **Questions**: Individual questions with Bloom's taxonomy levels, math formulas, and distractor analysis
- **Attempts**: Learner quiz attempts with answers, scores, and gap analysis

## 📋 Core Competencies Covered

| ID | Competency Name | Domain |
|----|----------------|--------|
| OSS-STAT-01 | Survey Methodology & Sampling Frame Design | Knowledge |
| OSS-STAT-02 | Field Scrutiny & Schedule Validation | Functional |
| OSS-STAT-03 | Outlier Detection & Imputation Techniques | Functional |
| OSS-STAT-04 | Non-Sampling Error Minimization | Functional |
| OSS-STAT-05 | Data Quality Assurance & Audit Trails | Functional |
| OSS-STAT-06 | Official Statistics Standards & MoSPI Guidelines | Behavioral/Compliance |
| OSS-STAT-07 | Data Privacy, Confidentiality & Anonymization | Behavioral/Compliance |
| OSS-STAT-08 | Consumer Price Index & Index Numbers Compilation | Knowledge |
| OSS-STAT-09 | National Accounts & Gross State Domestic Product (GSDP) | Knowledge |
| OSS-STAT-10 | Statistical Dissemination & Dashboard Visualization | Functional |

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Google AI Studio API key (free tier available)

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/otter170708/StatskillAi.git
   cd StatskillAi/backend/backend
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and configure your settings:
   ```env
   AI_PROVIDER=gemini
   AI_API_KEY=your_gemini_api_key_here
   AI_MODEL_NAME=gemini-flash-latest
   ```

> 🔒 **Security Notice for Git Commits**:
> The `.env` file contains sensitive API keys and credentials. It is untracked from Git via `git rm --cached .env` and protected by `.gitignore`. **Never commit or push `.env` to public GitHub repositories.** Always use `.env.example` as a template.

4. **Run the Application**
   ```bash
   python run.py
   ```

5. **Access the Platform**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

### Getting Your Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key and paste it as `AI_API_KEY` in `.env`
4. The system connects to `gemini-flash-latest` with automated 15-second fast-fallback to verified MoSPI domain questions during demand spikes or rate limits.

## 📖 Usage Guide

### 1. Upload Training Material
- Navigate to Materials section
- Upload PDF or text documents (max 15MB)
- System extracts text and tags topics automatically

### 2. Generate Quiz
- Select uploaded material
- Choose quiz format (MCQ, Mixed Format)
- Set difficulty level and number of questions
- AI generates scenario-based questions grounded in material

### 3. Take Assessment
- Answer questions with confidence rating (Low/Medium/High)
- Submit for instant evaluation
- Receive detailed feedback with distractor analysis

### 4. View Diagnostics
- Access competency breakdown radar
- Review identified skill gaps with severity
- Understand misconceptions through detailed explanations

### 5. Enroll in Recommended Courses
- Browse iGOT Karmayogi course recommendations
- View course details and target competencies
- One-click enrollment with APAR ledger sync

### 6. Track Progress
- Monitor karma points and learning streaks
- Review historical attempt performance
- Generate official APAR compliance dossiers

## 🔧 API Endpoints

### Core Endpoints
- `POST /api/materials/upload` - Upload training materials
- `POST /api/quizzes/generate` - Generate AI-powered quizzes
- `POST /api/quizzes/{quiz_id}/attempt` - Submit quiz attempt
- `GET /api/learners/{learner_id}/dashboard` - Get learner dashboard
- `GET /api/learners/{learner_id}/dossier` - Generate official dossier
- `GET /api/courses` - Browse iGOT Karmayogi courses
- `POST /api/courses/{course_id}/enrol` - Enroll in course

### Documentation
Interactive API documentation available at `/docs` (Swagger UI)

## 🌐 Deployment

### Production Considerations
- Switch from SQLite to PostgreSQL for production
- Configure proper CORS origins
- Set up environment variables for security
- Enable HTTPS for production deployment
- Configure proper logging and monitoring

### Cloud Deployment
The application can be deployed to:
- AWS (EC2, Elastic Beanstalk)
- Google Cloud Platform (App Engine, Cloud Run)
- Azure (App Service, Container Instances)
- Heroku
- Railway

See `DEPLOYMENT.md` for detailed deployment guides.

## 📚 Official MoSPI Pre-Loaded Manuals

The platform comes pre-seeded with 6 authentic, distinct official training manuals covering India's primary statistical surveys, with automatic canonical deduplication in `GET /api/materials`:

1. **NSS 79th Round - Field Scrutiny & Sampling Guidelines** (`MAT-NSSO-79-SAMPLE`)
   - Stratified two-stage sampling, Circular Systematic Sampling (\(R + (j-1)k\)), 2-visit casualty rule, captive power verification in Schedule Block 3, Section 9 Collection of Statistics Act 2008 confidentiality.
2. **NSSTA Handbook on Data Quality Assurance & Audit Trails** (`MAT-NSSTA-QA-SAMPLE`)
   - CAPI Soft vs. Hard check enforcement logic, Index of Inconsistency (IoI) thresholds, primary and complementary (secondary) cell suppression.
3. **Periodic Labour Force Survey (PLFS) - CAPI Field Scrutiny Manual** (`MAT-PLFS-CAPI-SAMPLE`)
   - Usual Principal Activity (365 days) vs. Current Daily Status (7 days), Unemployment Rate (\(\text{UR} = \frac{\text{Unemployed}}{\text{Labor Force}} \times 100\)), labor force participation.
4. **Household Consumption Expenditure Survey (HCES) - Estimation & Scrutiny Handbook** (`MAT-HCES-EXP-SAMPLE`)
   - Modified Mixed Reference Period (MMRP 7d/30d/365d), home-grown agricultural produce farm-gate valuation, ceremonial expenditure outlier weighting.
5. **Consumer Price Index (CPI-Rural/Urban) - Price Collection & Imputation Manual** (`MAT-CPI-MAN-SAMPLE`)
   - Jevons elementary index (geometric mean of price relatives), Laspeyres base quantity weighting, missing item sub-group relative imputation.
6. **Annual Survey of Industries (ASI) - Factory Schedule & GVA Compilation Manual** (`MAT-ASI-FAC-SAMPLE`)
   - 5-digit NIC-2008 Principal Activity rule (highest GVA), Gross Value Added accounting (\(\text{Gross Output} - \text{Intermediate Consumption}\)), double deflation.

## 🧮 Statistical Feasibility & Verification (25 Core Scenarios)

When generating quizzes in standard/preset mode (without custom document upload), StatSkill AI draws from a rigorously verified pool of 25 workplace dilemmas mapped to Indian Statistical Service (ISS / SSS) standards:
- **Exact Mathematical Calculations**: Unemployment Rate (\(\text{UR} = 10.0\%\)), ASI Gross Value Added (\(\text{GVA} = \text{₹40 Lakhs}\)), Circular Systematic Sampling sequences, Neyman Optimal Allocation (\(n_h \propto N_h S_h\)).
- **Official Legal Standards**: Section 9 Collection of Statistics Act (k-anonymity & l-diversity), NIC-2008 classification, SDMX machine-readable standard.
- **Pedagogical Distractor Analysis**: Detailed explanation for every incorrect option pinpointing specific conceptual misconceptions.

## 🏆 Smart India Hackathon (SIH 2026) Red Flag Mitigations

| # | SIH Disqualification Red Flag | Technical Mitigation Implemented |
|---|---|---|
| **1** | **Git Credential Leakage** | `.env` untracked from Git (`git rm --cached .env`) and protected via `.gitignore`. Public repo only contains `.env.example`. |
| **2** | **Repeated Ingest Materials** | Automatic title deduplication in `GET /api/materials` and upload endpoints; cleaned database of test duplicates. |
| **3** | **Unfeasible / Trivial AI Questions** | 25 verified MoSPI scenarios covering all 10 FRAC competencies with exact formulas and authentic survey protocols. |
| **4** | **Live Pitch 503 / 429 Demands** | Snappy 15-second timeout with instant fallback to verified MoSPI domain questions (0 UI delays, 0 crashes). |
| **5** | **Model Deprecation 404** | Updated to `gemini-flash-latest` (HTTP 200 verified) replacing discontinued `gemini-2.5-flash`. |
| **6** | **Institutional Alignment** | 1-Click iGOT Karmayogi Course Enrolment bridge, FRAC 10-Dimensional Radar Chart, and MoSPI APAR Competency Dossier export. |
| **7** | **Code Instability** | 19-step automated test suite (`test_api.py`) runs 100% clean with all 19 tests passing. |

## 🧪 Automated Verification & Testing

The backend includes a comprehensive 19-step automated test suite that validates everything end-to-end:

```bash
python test_api.py
```

**Test Coverage Highlights**:
- Step 1–5: Health, competencies, iGOT courses, demo learners, and deduplicated materials
- Step 6–8: Quiz generation, diagnostic engine, gap analysis, and learning streak tracking
- Step 9–11: SME Human-in-the-loop review gatekeeper and image OCR ingestion
- Step 12–16: Diverse personas, karma point accumulation, single-day streak invariants, and post-test payloads
- Step 17: Grounded custom material MCQs (non-True/False)
- Step 18: Live iGOT Karmayogi enrolment webhook
- Step 19: MoSPI APAR official dossier generation with SHA-256 digital seal

## 📊 Project Impact

### For Civil Servants
- **Personalized Learning**: Targeted skill development based on actual gaps
- **Time Efficiency**: Focus on relevant competencies, not generic training
- **Career Growth**: Clear competency progression tracking with APAR alignment
- **Engagement**: Gamified learning with points and streaks

### For Training Administrators
- **Scalability**: Automate assessment creation from any training material
- **Quality Assurance**: SME review workflow ensures content accuracy
- **Data-Driven Insights**: Aggregate analytics on workforce competencies
- **Compliance**: Automated APAR competency tracking

### For Statistical System
- **Standardization**: Consistent assessment standards across offices
- **Capacity Building**: Systematic approach to skill development
- **Knowledge Management**: Centralized repository of assessed competencies
- **Performance Measurement**: Objective metrics for training effectiveness

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is developed for the Smart India Hackathon 2026 and is available for educational and governmental use.

## 👥 Team

**StatSkill AI Team** - Smart India Hackathon 2026 Participants

## 🙏 Acknowledgments

- **Ministry of Statistics and Programme Implementation (MoSPI)** - Domain expertise and requirements
- **iGOT Karmayogi Platform** - Integration support and course catalog
- **National Statistical Systems Training Academy (NSSTA)** - Training framework alignment
- **Google AI** - Gemini API for AI-powered assessment generation

## 📞 Support

For queries and support:
- GitHub Issues: https://github.com/otter170708/StatskillAi/issues
- Documentation: See `ARCHITECTURE.md` and `API.md` for technical details

---

**Built with ❤️ for India's Digital Statistical Transformation**