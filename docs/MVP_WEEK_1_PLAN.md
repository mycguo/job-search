# 🚀 Job Search Agent - MVP Week 1 Plan

## Goal
Transform your AI Assistant into a functional Job Search Agent in **7 days**.

---

## Day 1: Application Data Model & Storage

### Tasks
- [x] Create `models/application.py`
- [x] Create `storage/json_db.py`
- [x] Basic CRUD operations

### Code Structure

```python
# models/application.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

@dataclass
class Application:
    id: str
    company: str
    role: str
    status: str  # applied, screening, interview, offer, rejected, withdrawn
    applied_date: str
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    match_score: Optional[float] = None
    notes: Optional[str] = None

    def to_dict(self):
        return asdict(self)
```

```python
# storage/json_db.py
import json
import os
from typing import List, Optional
from models.application import Application

class JobSearchDB:
    def __init__(self, data_dir="./job_search_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.applications_file = os.path.join(data_dir, "applications.json")

    def add_application(self, app: Application) -> str:
        """Add new application and return ID"""
        pass

    def get_application(self, app_id: str) -> Optional[Application]:
        """Get application by ID"""
        pass

    def list_applications(self, status: Optional[str] = None) -> List[Application]:
        """List all applications, optionally filtered by status"""
        pass

    def update_status(self, app_id: str, new_status: str):
        """Update application status"""
        pass
```

### Deliverable
✅ Working storage layer with basic operations

---

## Day 2: Application UI

### Tasks
- [x] Create `pages/applications.py`
- [x] Add application form
- [x] List view with filters
- [x] Status update buttons

### UI Layout

```python
# pages/applications.py
import streamlit as st
from storage.json_db import JobSearchDB

def main():
    st.title("📝 Job Applications")

    # Add new application
    with st.expander("➕ Add New Application", expanded=False):
        with st.form("new_application"):
            company = st.text_input("Company *")
            role = st.text_input("Role *")
            col1, col2 = st.columns(2)
            with col1:
                location = st.text_input("Location")
                salary = st.text_input("Salary Range")
            with col2:
                job_url = st.text_input("Job URL")
                applied_date = st.date_input("Applied Date")

            job_desc = st.text_area("Job Description", height=100)
            notes = st.text_area("Notes", height=50)

            if st.form_submit_button("Add Application"):
                # Save to DB
                st.success("Application added!")

    # Filter applications
    st.subheader("Your Applications")
    filter_status = st.selectbox(
        "Filter by status:",
        ["All", "Applied", "Screening", "Interview", "Offer", "Rejected"]
    )

    # List applications
    db = JobSearchDB()
    applications = db.list_applications()

    for app in applications:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.markdown(f"**{app.company}** - {app.role}")
                if app.location:
                    st.caption(app.location)
            with col2:
                st.write(f"📅 {app.applied_date}")
            with col3:
                # Status badge with color
                status_colors = {
                    "applied": "🔵",
                    "screening": "🟡",
                    "interview": "🟠",
                    "offer": "🟢",
                    "rejected": "🔴"
                }
                st.write(f"{status_colors.get(app.status, '⚪')} {app.status.title()}")
            with col4:
                if st.button("Update", key=f"update_{app.id}"):
                    # Show update dialog
                    pass

            if app.notes:
                with st.expander("Notes"):
                    st.write(app.notes)

            st.divider()
```

### Deliverable
✅ Full CRUD UI for applications

---

## Day 3: Job Description Analysis

### Tasks
- [x] Create `ai/job_matcher.py`
- [x] Extract requirements from job description
- [x] Calculate match score
- [x] Integration with application form

### Code Structure

```python
# ai/job_matcher.py
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, List

class JobMatcher:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3
        )

    def extract_requirements(self, job_description: str) -> Dict:
        """
        Extract structured data from job description:
        - Required skills
        - Preferred skills
        - Experience level
        - Education requirements
        - Key responsibilities
        """
        prompt = f"""
        Analyze this job description and extract:

        1. Required Skills (must-have)
        2. Preferred Skills (nice-to-have)
        3. Years of Experience Required
        4. Education Requirements
        5. Key Responsibilities (top 3)
        6. Company Culture Keywords

        Job Description:
        {job_description}

        Return as structured JSON.
        """

        response = self.model.invoke(prompt)
        # Parse and return structured data
        return parse_job_requirements(response.content)

    def calculate_match_score(self, job_requirements: Dict, user_profile: Dict) -> float:
        """
        Calculate 0-1 match score based on:
        - Skill alignment (50%)
        - Experience match (30%)
        - Location preference (10%)
        - Other factors (10%)
        """
        prompt = f"""
        Calculate a match score (0-100) between this job and candidate profile.

        Job Requirements:
        {job_requirements}

        Candidate Profile:
        {user_profile}

        Consider:
        - Required skills match
        - Experience level alignment
        - Location preferences
        - Salary expectations

        Return JSON with:
        - score (0-100)
        - matching_skills: [list]
        - missing_skills: [list]
        - reasoning: string
        """

        response = self.model.invoke(prompt)
        return parse_match_score(response.content)
```

### Deliverable
✅ AI-powered job analysis and matching

---

## Day 4: Enhanced Remember Feature

### Tasks
- [x] Update remember feature for job search
- [x] Auto-detect application tracking
- [x] Auto-detect interview scheduling
- [x] Add to main chat

### Patterns to Detect

```python
# Add to app.py detect_remember_intent()

job_search_patterns = [
    # Application tracking
    r'^applied to\s+(.+)\s+(?:for|as)\s+(.+)',
    r'^submitted application to\s+(.+)',

    # Interview scheduling
    r'^interview with\s+(.+)\s+(?:at|for)\s+(.+)\s+on\s+(.+)',
    r'^phone screen with\s+(.+)',

    # Company notes
    r'^(.+)\s+offers\s+(.+)',
    r'^(.+)\s+uses\s+(.+)',
]

# Examples that should work:
"Applied to Google for ML Engineer"
-> Create application entry

"Interview with Jane at Meta on Nov 10 at 2pm"
-> Create interview entry

"Remember Google offers 20% time"
-> Save as company note
```

### Enhanced Processing

```python
def process_job_search_command(text: str):
    """
    Process job search specific commands:
    - Application tracking
    - Interview scheduling
    - Company notes
    """

    # Detect application
    if "applied to" in text.lower():
        company, role = extract_application_info(text)
        db = JobSearchDB()
        db.add_application(Application(
            id=generate_id(),
            company=company,
            role=role,
            status="applied",
            applied_date=datetime.now().strftime("%Y-%m-%d"),
            notes=text
        ))
        return f"✅ Tracked application to {company} for {role}"

    # Detect interview
    if "interview" in text.lower():
        interview_info = extract_interview_info(text)
        # Schedule interview
        return f"📅 Interview scheduled: {interview_info}"

    # Default to general remember
    return save_to_knowledge_base(text)
```

### Deliverable
✅ Natural language job tracking

---

## Day 5: Chat Interface Integration

### Tasks
- [x] Update main chat for job search
- [x] Add quick actions
- [x] Context-aware responses
- [x] Query applications from chat

### Chat Enhancements

```python
# app.py main()

st.title("🎯 Job Search Agent")

# Quick actions in sidebar
with st.sidebar:
    st.header("⚡ Quick Actions")

    if st.button("➕ Add Application"):
        st.session_state['show_add_form'] = True

    if st.button("📋 View Applications"):
        st.switch_page("pages/applications.py")

    if st.button("📊 Dashboard"):
        # Show dashboard
        pass

    st.divider()

    # Stats
    db = JobSearchDB()
    apps = db.list_applications()
    st.metric("Total Applications", len(apps))
    st.metric("Active", len([a for a in apps if a.status in ["applied", "screening", "interview"]]))

# Main chat
user_question = st.text_input(
    "Ask anything or track your job search:",
    placeholder="Examples: 'Applied to Google today' or 'What jobs should I apply to?'"
)

if user_question:
    # Check if job search command
    is_job_command, result = process_job_search_command(user_question)

    if is_job_command:
        st.success(result)
    else:
        # Normal RAG query
        user_input(user_question)
```

### Example Interactions

```
User: "Applied to Google for ML Engineer on Nov 1"
Agent: ✅ Tracked application to Google for ML Engineer
      Status: Applied | Date: Nov 1, 2025
      [View Details] [Add Notes]

User: "What companies have I applied to?"
Agent: You've applied to 5 companies:
       1. Google - ML Engineer (Applied, Nov 1)
       2. Meta - Senior Engineer (Screening, Nov 3)
       3. OpenAI - AI Engineer (Interview, Oct 28)
       4. Anthropic - Senior Engineer (Offer, Oct 25)
       5. Stripe - Backend Engineer (Applied, Nov 5)

User: "Generate a cover letter for Google"
Agent: Here's a tailored cover letter for your Google ML Engineer application:
       [Shows cover letter]
       [Copy] [Edit] [Save to Application]
```

### Deliverable
✅ Fully integrated chat interface

---

## Day 6: Dashboard & Analytics

### Tasks
- [x] Create `pages/dashboard.py`
- [x] Application statistics
- [x] Pipeline visualization
- [x] Action items

### Dashboard Layout

```python
# pages/dashboard.py
import streamlit as st
import plotly.express as px
from storage.json_db import JobSearchDB

def main():
    st.title("📊 Dashboard")

    db = JobSearchDB()
    apps = db.list_applications()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Applications", len(apps))
    with col2:
        active = len([a for a in apps if a.status in ["applied", "screening", "interview"]])
        st.metric("Active", active)
    with col3:
        offers = len([a for a in apps if a.status == "offer"])
        st.metric("Offers", offers)
    with col4:
        response_rate = len([a for a in apps if a.status != "applied"]) / max(len(apps), 1) * 100
        st.metric("Response Rate", f"{response_rate:.1f}%")

    # Pipeline visualization
    st.subheader("Application Pipeline")
    status_counts = {}
    for app in apps:
        status_counts[app.status] = status_counts.get(app.status, 0) + 1

    fig = px.funnel(
        y=["Applied", "Screening", "Interview", "Offer"],
        x=[status_counts.get(s.lower(), 0) for s in ["applied", "screening", "interview", "offer"]]
    )
    st.plotly_chart(fig)

    # Action items
    st.subheader("🔥 Action Items")
    # TODO: Add follow-up reminders
    st.info("No pending actions")

    # Recent activity
    st.subheader("Recent Activity")
    sorted_apps = sorted(apps, key=lambda x: x.applied_date, reverse=True)[:5]
    for app in sorted_apps:
        st.write(f"**{app.company}** - {app.role} ({app.status})")
```

### Deliverable
✅ Visual dashboard with metrics

---

## Day 7: Testing & Polish

### Tasks
- [x] End-to-end testing
- [x] Bug fixes
- [x] Documentation
- [x] Demo preparation

### Test Checklist

```
Application Management:
☐ Add new application
☐ Update application status
☐ Filter applications by status
☐ View application details
☐ Add notes to application

Natural Language:
☐ "Applied to Google for ML Engineer"
☐ "What companies have I applied to?"
☐ "Show me applications in interview stage"

AI Features:
☐ Job description analysis
☐ Match score calculation
☐ Cover letter generation (if implemented)

Dashboard:
☐ Metrics display correctly
☐ Pipeline visualization works
☐ Recent activity shows latest

Data Persistence:
☐ Applications saved correctly
☐ Data survives app restart
☐ JSON files readable
```

### Documentation

Create `README_JOB_SEARCH.md` with:
- Getting started
- How to add applications
- Natural language commands
- Screenshots

### Deliverable
✅ Tested, documented MVP

---

## 🎉 End of Week 1

You'll have a working Job Search Agent with:

✅ Application tracking (CRUD)
✅ Natural language commands ("Applied to Google...")
✅ AI-powered job matching
✅ Dashboard with analytics
✅ Enhanced chat interface

**Ready to manage your entire job search!**

---

## Quick Start Commands

```bash
# Day 1-2: Create basic structure
mkdir -p models storage pages ai
touch models/application.py storage/json_db.py pages/applications.py

# Day 3: Add AI features
touch ai/job_matcher.py

# Day 6: Add dashboard
touch pages/dashboard.py

# Day 7: Test everything
streamlit run app.py
```

---

## Next Week

Once MVP is complete, move to:
- Interview scheduling
- Contact management
- Resume tailoring
- Cover letter generation
- Advanced analytics

**Focus on getting MVP working first!**
