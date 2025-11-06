# 🎯 Job Search Agent - Transformation Plan

## Executive Summary

Transform the AI Knowledge Assistant into a comprehensive Job Search Agent that helps manage your entire job search journey - from resume optimization to interview preparation to offer negotiation.

---

## 📊 Current System Analysis

### ✅ What We Already Have (Leverage These)

| Feature | Current Use | Job Search Use |
|---------|-------------|----------------|
| **Document Ingestion** | PDFs, Word, Excel | Resumes, job descriptions, offer letters |
| **Vector Store** | Knowledge base | Job postings, company research, notes |
| **RAG System** | Q&A on documents | "What roles match my skills?", "Tell me about Company X" |
| **Remember Feature** | Save quick facts | "Remember I applied to Google on Nov 1", "Note: Interview with Jane Doe tomorrow" |
| **Web Crawler** | Fetch web content | Scrape job postings, company pages, LinkedIn |
| **LLM (Gemini 2.5)** | Answer questions | Cover letter generation, resume tailoring, interview prep |
| **Embeddings** | Semantic search | Match skills to jobs, find similar companies |
| **Streamlit UI** | Chat + Admin | Dashboard + Job Pipeline + Analytics |

### 🔧 What Needs to Change

1. **Data Model**: Add job-specific entities (applications, interviews, contacts)
2. **UI/UX**: Transform from Q&A to job pipeline management
3. **Features**: Add job-search-specific workflows
4. **Context**: Reframe all prompts for job search domain
5. **Analytics**: Add metrics and tracking

---

## 🎯 Job Search Agent - Core Features

### Phase 1: Foundation (Week 1-2)

#### 1.1 Data Models & Schema

**Job Application Entity**
```python
{
    "id": "app_001",
    "company": "Google",
    "role": "Senior AI Engineer",
    "location": "San Francisco, CA",
    "status": "applied" | "screening" | "interview" | "offer" | "rejected" | "withdrawn",
    "applied_date": "2025-11-01",
    "job_url": "https://...",
    "job_description": "...",
    "salary_range": "$180k-$250k",
    "match_score": 0.85,  # How well it matches your profile
    "notes": "Referred by John",
    "timeline": [
        {"date": "2025-11-01", "event": "Applied", "notes": "..."},
        {"date": "2025-11-05", "event": "Phone Screen", "notes": "..."}
    ]
}
```

**Contact/Network Entity**
```python
{
    "id": "contact_001",
    "name": "Jane Doe",
    "role": "Engineering Manager at Google",
    "company": "Google",
    "relationship": "Former colleague",
    "contact_info": "jane@example.com",
    "linkedin": "https://linkedin.com/in/janedoe",
    "interactions": [
        {"date": "2025-10-15", "type": "Coffee chat", "notes": "..."}
    ],
    "can_refer": true
}
```

**Interview Entity**
```python
{
    "id": "interview_001",
    "application_id": "app_001",
    "company": "Google",
    "date": "2025-11-10T14:00:00",
    "type": "Technical" | "Behavioral" | "System Design" | "Cultural Fit",
    "interviewer": "Jane Doe",
    "status": "scheduled" | "completed" | "cancelled",
    "preparation_notes": "...",
    "questions_asked": ["Tell me about...", "How would you design..."],
    "performance_notes": "...",
    "follow_up": "Send thank you email"
}
```

**Your Profile Entity**
```python
{
    "resumes": {
        "general": {"path": "...", "last_updated": "..."},
        "ai_focused": {"path": "...", "last_updated": "..."},
        "backend_focused": {"path": "...", "last_updated": "..."}
    },
    "skills": {
        "primary": ["Python", "AI/ML", "LangChain", "RAG Systems"],
        "secondary": ["JavaScript", "React", "Docker"],
        "learning": ["Kubernetes", "System Design"]
    },
    "experience": [
        {"company": "...", "role": "...", "duration": "...", "achievements": ["..."]}
    ],
    "preferences": {
        "roles": ["AI Engineer", "ML Engineer", "Senior Backend Engineer"],
        "locations": ["San Francisco", "Remote"],
        "salary_min": 180000,
        "company_size": ["startup", "mid-size"],
        "visa_sponsorship": false
    },
    "target_companies": ["Google", "OpenAI", "Anthropic", "..."]
}
```

#### 1.2 Database Layer

**New Storage Structure**
```
./job_search_data/
├── applications.json       # All applications
├── contacts.json          # Network contacts
├── interviews.json        # Interview schedule
├── profile.json          # Your profile
├── companies/            # Company research
│   ├── google.json
│   └── openai.json
└── documents/
    ├── resumes/
    ├── cover_letters/
    └── job_descriptions/
```

#### 1.3 Core Functions

```python
# Application Management
add_application(company, role, url, description, ...)
update_application_status(app_id, new_status)
get_applications(status=None, company=None)
get_application_timeline(app_id)

# Contact Management
add_contact(name, company, relationship, ...)
log_interaction(contact_id, type, notes)
find_contacts_at_company(company)

# Interview Management
schedule_interview(app_id, date, type, interviewer)
add_interview_notes(interview_id, notes)
get_upcoming_interviews()

# Analytics
get_application_stats()
get_response_rate_by_company()
get_average_time_to_response()
calculate_match_score(job_description, your_profile)
```

---

### Phase 2: Intelligence Layer (Week 3-4)

#### 2.1 AI-Powered Features

**Resume Tailoring**
```python
def tailor_resume(job_description, base_resume):
    """
    Analyze job description and customize resume:
    - Highlight relevant skills
    - Reorder experience by relevance
    - Adjust keywords for ATS
    - Return tailored version + explanation
    """
```

**Cover Letter Generation**
```python
def generate_cover_letter(job_description, company_info, your_experience):
    """
    Generate personalized cover letter:
    - Reference company mission/values
    - Align experience with requirements
    - Show enthusiasm and culture fit
    - Professional but authentic tone
    """
```

**Job Matching & Recommendations**
```python
def calculate_job_match(job_description, your_profile):
    """
    Return match score (0-1) based on:
    - Skills alignment
    - Experience level
    - Location preferences
    - Salary expectations
    - Company size/culture
    """

def recommend_jobs():
    """
    Suggest jobs from knowledge base:
    - High match score
    - Not yet applied
    - Within preferences
    """
```

**Interview Preparation**
```python
def prepare_for_interview(company, role, interview_type):
    """
    Generate:
    - Common questions for role/company
    - STAR method answers using your experience
    - Questions to ask interviewer
    - Company-specific talking points
    """

def practice_interview(role, difficulty="medium"):
    """
    Interactive interview practice:
    - Ask realistic questions
    - Provide feedback on answers
    - Suggest improvements
    """
```

**Company Research**
```python
def research_company(company_name):
    """
    Gather and summarize:
    - Company mission, values, culture
    - Recent news and developments
    - Tech stack and engineering blog
    - Interview process and timeline
    - Glassdoor reviews summary
    """
```

**Salary Negotiation**
```python
def salary_analysis(role, location, experience_years):
    """
    Provide:
    - Market rate range
    - Your position (below/at/above market)
    - Negotiation talking points
    - Comp package breakdown (base/equity/bonus)
    """
```

#### 2.2 Enhanced Remember Feature

Contextualized for job search:

```python
# Detect job search intents
"Remember I applied to Google for ML Engineer role on Nov 1"
"Note: Phone screen with Jane tomorrow at 2pm"
"Store that Google offers 20% time for side projects"
"Remember: Sarah from Meta said they're hiring in Q1"
"Note: Need to follow up with recruiter by Friday"
```

Auto-categorization:
- Application tracking
- Interview notes
- Company insights
- Network activity
- Follow-up reminders

---

### Phase 3: UI Transformation (Week 5-6)

#### 3.1 New Dashboard Layout

**Main Navigation**
```
┌─────────────────────────────────────────────┐
│  🎯 Job Search Agent                        │
├─────────────────────────────────────────────┤
│  📊 Dashboard  │  📝 Applications  │  📅 Calendar  │  🤝 Network  │  💡 Insights  │
└─────────────────────────────────────────────┘
```

**Dashboard View**
```
┌─────────────────────────────────────────────┐
│  📊 Overview                                │
├─────────────────────────────────────────────┤
│  Active Applications: 12                    │
│  Interviews This Week: 3                    │
│  Response Rate: 35%                         │
│  Average Time to Response: 5 days          │
├─────────────────────────────────────────────┤
│  🔥 Action Items                            │
│  ☐ Follow up with Google (3 days)          │
│  ☐ Interview prep for Meta (Tomorrow)      │
│  ☐ Submit application to OpenAI            │
├─────────────────────────────────────────────┤
│  📈 Pipeline                                │
│  Applied: ████████ 8                        │
│  Screening: ████ 2                          │
│  Interview: ██ 2                            │
│  Offer: █ 1                                 │
└─────────────────────────────────────────────┘
```

#### 3.2 Applications Kanban Board

```
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Applied │Screening│Interview│  Offer  │ Closed  │
├─────────┼─────────┼─────────┼─────────┼─────────┤
│ Google  │  Meta   │ OpenAI  │Anthropic│         │
│  ML Eng │ Sr Eng  │ AI Eng  │ Sr Eng  │         │
│ 85% ⭐  │ 90% ⭐  │ 78% ⭐  │ 95% ⭐  │         │
│ Nov 1   │ Nov 3   │ Oct 28  │ Oct 25  │         │
├─────────┼─────────┼─────────┼─────────┼─────────┤
│ Stripe  │         │         │         │         │
│ Backend │         │         │         │         │
│ 75% ⭐  │         │         │         │         │
│ Nov 5   │         │         │         │         │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

#### 3.3 Interview Calendar

```
┌─────────────────────────────────────────────┐
│  📅 This Week                               │
├─────────────────────────────────────────────┤
│  Monday Nov 6                               │
│    2:00 PM - Google Phone Screen            │
│               Jane Doe (Recruiter)          │
│               [Prep Notes] [Join Call]      │
│                                             │
│  Wednesday Nov 8                            │
│    10:00 AM - Meta Technical Interview      │
│                [System Design Focus]        │
│                [Prep Notes] [Join Call]     │
└─────────────────────────────────────────────┘
```

#### 3.4 AI Assistant Chat

Enhanced for job search:

```
User: "What roles should I apply to next?"

Agent: 📊 Based on your profile, I recommend:

1. **Senior AI Engineer at Anthropic** (95% match)
   - Strong alignment with your RAG experience
   - Remote-friendly
   - $200k-$280k range
   [View Details] [Apply Now] [Tailor Resume]

2. **ML Engineer at OpenAI** (92% match)
   - Your LLM experience is highly relevant
   - San Francisco office
   - Competitive comp + equity
   [View Details] [Apply Now] [Tailor Resume]
```

---

### Phase 4: Workflows (Week 7-8)

#### 4.1 Application Workflow

```
1. Find Job → 2. Analyze Fit → 3. Tailor Resume → 4. Generate Cover Letter → 5. Apply → 6. Track
```

**Example Flow:**
```python
# User pastes job URL
job_url = "https://careers.anthropic.com/ai-engineer"

# System scrapes and analyzes
job_data = scrape_job_posting(job_url)
match_score = calculate_match(job_data, user_profile)

# Show analysis
"This role is a 95% match for you because:"
"✓ Requires Python, LLM, RAG (you have all)"
"✓ 5+ years experience (you have 7)"
"✓ Remote friendly (matches your preference)"
"⚠ Requires Kubernetes (you're learning)"

# Offer to prepare application
[Tailor Resume] [Generate Cover Letter] [Add to Applications]
```

#### 4.2 Interview Prep Workflow

```
1. Schedule → 2. Research → 3. Practice → 4. Prepare Questions → 5. Interview → 6. Follow-up
```

**Example:**
```
Interview Tomorrow: Google - ML Engineer
───────────────────────────────────────

📚 Preparation Checklist:
☑ Company research completed
☑ Technical questions practiced (15/20)
☐ Behavioral questions reviewed
☐ Questions for interviewer prepared
☐ Portfolio examples ready

💡 Quick Review:
- Google values: Innovation, user focus, scale
- Recent: Released Gemini 2.5 Flash
- Ask about: Team structure, project autonomy

🎯 Practice One More:
"Design a distributed caching system for..."
[Start Practice Session]
```

#### 4.3 Networking Workflow

```
User: "Who do I know at Google?"

Agent: 🤝 You have 3 contacts at Google:

1. **Jane Doe** - Engineering Manager
   - Former colleague at TechCorp
   - Last contact: Coffee chat (Oct 15)
   - Can refer: ✓
   [Reach Out] [View History]

2. **John Smith** - Senior Engineer
   - LinkedIn connection
   - Shared connection: Sarah
   [Request Introduction]

💡 Action: Jane Doe can refer you to the ML team!
[Draft referral request]
```

---

## 🚀 Implementation Roadmap

### Week 1-2: Foundation
- [ ] Design and implement data models
- [ ] Create JSON-based storage layer
- [ ] Build CRUD operations for applications/contacts/interviews
- [ ] Migrate remember feature to job search context
- [ ] Update vector store schema with job metadata

### Week 3-4: Intelligence
- [ ] Resume tailoring function
- [ ] Cover letter generation
- [ ] Job matching algorithm
- [ ] Interview question generator
- [ ] Company research aggregator

### Week 5-6: UI/UX
- [ ] Dashboard with metrics
- [ ] Kanban board for applications
- [ ] Interview calendar view
- [ ] Network/contacts page
- [ ] Enhanced chat interface

### Week 7-8: Workflows
- [ ] End-to-end application workflow
- [ ] Interview preparation workflow
- [ ] Networking workflow
- [ ] Offer comparison tool
- [ ] Analytics and insights

### Week 9-10: Polish & Testing
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Demo/tutorial
- [ ] Performance optimization
- [ ] Deploy

---

## 📝 Specific File Changes

### New Files to Create

```
job_search_agent/
├── models/
│   ├── application.py      # Application data model
│   ├── contact.py          # Contact data model
│   ├── interview.py        # Interview data model
│   └── profile.py          # User profile model
├── storage/
│   ├── json_db.py          # JSON database handler
│   └── vector_store.py     # Enhanced vector store
├── ai/
│   ├── resume_tailor.py    # Resume customization
│   ├── cover_letter.py     # Cover letter generation
│   ├── job_matcher.py      # Job matching logic
│   ├── interview_prep.py   # Interview preparation
│   └── company_research.py # Company research
├── workflows/
│   ├── application.py      # Application workflow
│   ├── interview.py        # Interview workflow
│   └── networking.py       # Networking workflow
└── pages/
    ├── dashboard.py        # Main dashboard
    ├── applications.py     # Application kanban
    ├── calendar.py         # Interview calendar
    ├── network.py          # Network page
    └── insights.py         # Analytics page
```

### Files to Modify

```
✏️ app.py
- Rebrand as "Job Search Agent"
- Add job search context to chat
- Update remember feature for job search
- Add quick actions (add application, schedule interview)

✏️ simple_vector_store.py
- Add metadata fields for job search
- Add filtering by job type/company/status

✏️ CLAUDE.md
- Update project description
- Document job search features
- Add new architecture diagrams
```

---

## 🎯 Quick Wins (Start Here)

### Minimal Viable Product (MVP) - 1 Week

Focus on essentials:

1. **Application Tracking** (2 days)
   - JSON storage for applications
   - Add/update/view applications
   - Simple list view with status

2. **Job Description Analysis** (2 days)
   - Paste job URL or description
   - Extract requirements
   - Calculate match score
   - Save to knowledge base

3. **Remember Feature for Jobs** (1 day)
   - "Remember I applied to Google on Nov 1"
   - "Note: Interview with Jane tomorrow"
   - Auto-create application entries

4. **Chat Interface** (2 days)
   - "What jobs have I applied to?"
   - "When is my next interview?"
   - "Generate a cover letter for Google"

This gives you a functional job tracker with AI assistance in 1 week!

---

## 💡 Advanced Features (Future)

### Phase 2 Enhancements
- [ ] Email integration (auto-track applications from Gmail)
- [ ] LinkedIn integration (scrape profiles, auto-apply)
- [ ] ATS keyword optimization
- [ ] Automated follow-ups
- [ ] Salary negotiation coach
- [ ] Offer comparison matrix
- [ ] Job market trends analysis

### Phase 3 Integrations
- [ ] Calendar integration (Google Calendar for interviews)
- [ ] Job boards (Indeed, LinkedIn, AngelList)
- [ ] GitHub integration (showcase projects)
- [ ] Mock interview video recording
- [ ] Voice-based interview practice

---

## 📊 Success Metrics

Track effectiveness:
- Applications submitted per week
- Response rate (%)
- Average time to first response
- Interview conversion rate
- Offer acceptance rate
- Time saved vs manual tracking
- User satisfaction score

---

## 🤔 Decision Points

### UI Framework
- **Current**: Streamlit (good for MVP)
- **Future**: Consider Next.js for more interactive UI?

### Data Storage
- **Phase 1**: JSON files (simple, fast)
- **Phase 2**: SQLite (relationships, queries)
- **Phase 3**: PostgreSQL (production scale)

### Deployment
- **Local**: Good for personal use
- **Cloud**: Streamlit Cloud / Railway / Fly.io
- **Mobile**: Streamlit mobile? PWA?

---

## 🎉 End Goal

A comprehensive Job Search Agent that:

✅ Tracks all applications in one place
✅ Matches you with relevant jobs
✅ Generates tailored resumes & cover letters
✅ Prepares you for interviews
✅ Manages your professional network
✅ Provides analytics and insights
✅ Saves hours of manual work
✅ Increases your success rate

**Your personal AI recruiter and career coach!**

---

## Next Steps

1. Review this plan
2. Prioritize features (MVP vs future)
3. Start with Week 1-2 (Foundation)
4. Iterate based on your needs

Would you like me to start implementing any specific part?
