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
- **AI Engine**: Google Gemini 2.5 Flash (configurable for OpenAI, Anthropic)
- **Document Processing**: PyPDF for PDF text extraction
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend Stack
- **Framework**: Alpine.js (lightweight reactive framework)
- **Styling**: Tailwind CSS (utility-first CSS framework)
- **Charts**: Chart.js (data visualization)
- **Icons**: Lucide Icons
- **Fonts**: IBM Plex Sans & Mono (professional typography)

### Database Schema
- **Competencies**: 10 core statistical domains with difficulty levels
- **Courses**: iGOT Karmayogi course catalog with competency mappings
- **Learners**: Civil servant profiles with roles and departments
- **Materials**: Training documents with extracted text and topic tags
- **Quizzes**: Generated assessments with questions mapped to competencies
- **Questions**: Individual questions with Bloom's taxonomy levels and distractor analysis
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
   Edit `.env` and add your Gemini API key:
   ```env
   AI_PROVIDER=gemini
   AI_API_KEY=your_gemini_api_key_here
   AI_MODEL_NAME=gemini-2.5-flash
   ```

4. **Run the Application**
   ```bash
   python run.py
   ```

5. **Access the Platform**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

### Getting Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key" (no credit card required for free tier)
3. Copy your API key and add it to `.env`

**Free Tier Limits:**
- 15 requests/minute for Gemini Flash
- 1,500 requests/day for Gemini Flash
- Automatic retry with exponential backoff for rate limits

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

## 🧪 Testing

```bash
# Run API tests
python test_api.py

# Test specific endpoints
python -m pytest tests/
```

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