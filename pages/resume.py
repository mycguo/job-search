"""
Resume Management

Upload, view, and manage your resumes.
Future: AI-powered resume tailoring for specific jobs.
"""

import streamlit as st
import sys
from datetime import datetime
import io

# Add parent directory to path
sys.path.insert(0, '.')

from storage.resume_db import ResumeDB
from models.resume import create_resume, extract_skills_from_text, create_tailored_resume
from PyPDF2 import PdfReader
import docx
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
from bs4 import BeautifulSoup


def extract_text_from_resume_file(file_bytes, filename):
    """Extract text content from resume file"""
    try:
        file_lower = filename.lower()

        if file_lower.endswith('.pdf'):
            pdf = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text, 'pdf'

        elif file_lower.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_bytes))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text, 'docx'

        elif file_lower.endswith('.txt'):
            text = file_bytes.decode('utf-8')
            return text, 'txt'

        else:
            return None, None

    except Exception as e:
        st.error(f"Error extracting text: {str(e)}")
        return None, None


def fetch_job_description_from_url(url: str) -> tuple:
    """Fetch job description from URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract text from common job description containers
        # Try to find the main content area
        job_content = None

        # Common selectors for job descriptions
        selectors = [
            'div[class*="job-description"]',
            'div[class*="description"]',
            'div[id*="job-description"]',
            'article',
            'main',
            'div[class*="posting"]'
        ]

        for selector in selectors:
            job_content = soup.select_one(selector)
            if job_content:
                break

        if not job_content:
            # Fallback to body
            job_content = soup.find('body')

        # Extract text
        if job_content:
            # Remove script and style elements
            for script in job_content(["script", "style"]):
                script.decompose()

            text = job_content.get_text(separator='\n', strip=True)

            # Clean up extra whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)

            return True, text
        else:
            return False, "Could not extract job description from URL"

    except requests.exceptions.Timeout:
        return False, "Request timed out. Please try again or paste the job description manually."
    except requests.exceptions.RequestException as e:
        return False, f"Error fetching URL: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def tailor_resume_with_ai(resume_text: str, job_description: str, company_name: str = "") -> tuple:
    """Use AI to tailor resume for specific job"""
    try:
        model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

        prompt = f"""You are an expert resume writer. Tailor the following resume to match the job description below.

IMPORTANT INSTRUCTIONS:
1. Keep the same overall structure and format
2. Emphasize relevant experience and skills that match the job requirements
3. Add or highlight keywords from the job description
4. Quantify achievements where possible
5. Keep it concise and impactful
6. Maintain professional tone
7. Do NOT fabricate experience or skills
8. Only reframe and emphasize what's already in the resume

ORIGINAL RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

COMPANY: {company_name if company_name else "Not specified"}

Please provide the tailored resume text. Maintain the same structure but optimize the content to match the job requirements."""

        response = model.invoke(prompt)
        tailored_text = response.content.strip()

        # Extract any additional insights
        insights_prompt = f"""Based on the resume and job description, provide:
1. Top 3-5 keywords/skills from the job description that were emphasized in the tailored resume
2. A brief note about what was changed (2-3 sentences)

Format as:
KEYWORDS: keyword1, keyword2, keyword3
CHANGES: Brief description of changes made"""

        insights_response = model.invoke(insights_prompt)
        insights = insights_response.content.strip()

        return True, tailored_text, insights

    except Exception as e:
        return False, str(e), ""


def show_tailor_resume_form(db: ResumeDB):
    """Show form to tailor an existing resume for a specific job"""
    st.subheader("🎯 Tailor Resume for Job")
    st.markdown("Create a customized version of your resume tailored to a specific job posting")

    # Get all master resumes
    master_resumes = db.get_master_resumes()

    if not master_resumes:
        st.warning("No master resumes found. Please upload a master resume first!")
        return

    with st.form("tailor_resume_form", clear_on_submit=False):
        # Select master resume
        resume_options = {r.name: r for r in master_resumes}
        selected_resume_name = st.selectbox(
            "Select Master Resume *",
            options=list(resume_options.keys()),
            help="Choose the master resume to tailor"
        )

        selected_resume = resume_options[selected_resume_name]

        # Company and job info
        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input(
                "Company Name *",
                placeholder="e.g., Google, Microsoft, etc.",
                help="Company you're applying to"
            )

        with col2:
            job_title = st.text_input(
                "Job Title (optional)",
                placeholder="e.g., Senior Software Engineer",
                help="Position title"
            )

        # Job description input
        st.markdown("### Job Description")

        input_method = st.radio(
            "Input Method",
            ["Paste Description", "Fetch from URL"],
            horizontal=True
        )

        if input_method == "Paste Description":
            job_description = st.text_area(
                "Job Description *",
                placeholder="Paste the full job description here...",
                height=300,
                help="Paste the complete job posting"
            )
        else:
            job_url = st.text_input(
                "Job Posting URL *",
                placeholder="https://...",
                help="URL to the job posting"
            )
            job_description = ""

        # Additional notes
        tailoring_notes = st.text_area(
            "Tailoring Notes (optional)",
            placeholder="Any specific aspects you want to emphasize...",
            height=100
        )

        submit = st.form_submit_button("🎯 Tailor Resume", type="primary")

        if submit:
            if not company_name:
                st.error("⚠️ Please provide the company name!")
                return

            # Get job description
            if input_method == "Fetch from URL":
                if not job_url:
                    st.error("⚠️ Please provide a job posting URL!")
                    return

                with st.spinner("Fetching job description from URL..."):
                    success, result = fetch_job_description_from_url(job_url)

                    if not success:
                        st.error(f"❌ {result}")
                        return

                    job_description = result
                    st.success("✅ Job description fetched successfully!")

                    with st.expander("📄 Fetched Job Description"):
                        st.text(job_description[:1000] + "..." if len(job_description) > 1000 else job_description)

            if not job_description:
                st.error("⚠️ Please provide a job description!")
                return

            # Tailor the resume
            with st.spinner("✨ AI is tailoring your resume... This may take 15-30 seconds"):
                success, tailored_text, insights = tailor_resume_with_ai(
                    selected_resume.full_text,
                    job_description,
                    company_name
                )

                if not success:
                    st.error(f"❌ Error tailoring resume: {tailored_text}")
                    return

                # Create tailored resume
                tailored_resume = create_tailored_resume(
                    master_resume=selected_resume,
                    job_id="",  # Optional: link to job application
                    company=company_name,
                    tailoring_notes=tailoring_notes
                )

                # Update with tailored content
                tailored_resume.full_text = tailored_text
                tailored_resume.skills = extract_skills_from_text(tailored_text)

                if job_title:
                    tailored_resume.name = f"{company_name} - {job_title}"
                else:
                    tailored_resume.name = f"{company_name} Resume"

                # Save to database (no file bytes for tailored resumes)
                resume_id = db.add_resume(tailored_resume, None)

                st.success(f"✅ Resume tailored successfully! (ID: {resume_id})")

                # Show insights
                if insights:
                    with st.expander("💡 Tailoring Insights"):
                        st.markdown(insights)

                # Show preview
                with st.expander("📄 Tailored Resume Preview"):
                    st.text_area(
                        "Preview",
                        value=tailored_text[:2000] + "..." if len(tailored_text) > 2000 else tailored_text,
                        height=400,
                        disabled=True
                    )

                st.balloons()
                st.info("💡 You can view and download the tailored resume from the resume list")


def show_upload_resume_form(db: ResumeDB):
    """Show form to upload new resume"""
    st.subheader("📤 Upload Resume")

    with st.form("upload_resume_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "Choose your resume file",
                type=['pdf', 'docx', 'txt'],
                help="Upload your resume in PDF, Word, or Text format"
            )

        with col2:
            resume_name = st.text_input(
                "Resume Name *",
                placeholder="e.g., Software Engineer Resume",
                help="Give this resume a descriptive name"
            )

        col1, col2 = st.columns(2)

        with col1:
            is_master = st.checkbox(
                "Master Resume",
                value=True,
                help="Check if this is your master/template resume"
            )

        with col2:
            is_active = st.checkbox(
                "Set as Active",
                value=True,
                help="Use this resume for new applications"
            )

        notes = st.text_area(
            "Notes (optional)",
            placeholder="Any notes about this resume...",
            height=80
        )

        submit = st.form_submit_button("Upload Resume", type="primary")

        if submit:
            if not uploaded_file or not resume_name:
                st.error("⚠️ Please provide both a file and resume name!")
                return

            with st.spinner("Processing resume..."):
                # Read file
                file_bytes = uploaded_file.read()

                # Extract text
                text_content, file_type = extract_text_from_resume_file(
                    file_bytes,
                    uploaded_file.name
                )

                if not text_content:
                    st.error("Could not extract text from file. Please check the file format.")
                    return

                # Extract skills
                skills = extract_skills_from_text(text_content)

                # Create resume
                resume = create_resume(
                    name=resume_name,
                    full_text=text_content,
                    original_filename=uploaded_file.name,
                    file_type=file_type,
                    skills=skills,
                    is_master=is_master
                )

                resume.is_active = is_active

                # Save to database
                resume_id = db.add_resume(resume, file_bytes)

                st.success(f"✅ Resume uploaded successfully! (ID: {resume_id})")

                if skills:
                    with st.expander("🔍 Detected Skills"):
                        st.write(", ".join(skills))

                with st.expander("📄 Resume Preview"):
                    st.text(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)

                st.balloons()
                st.rerun()


def show_resume_list(db: ResumeDB):
    """Show list of all resumes"""
    resumes = db.list_resumes()

    if not resumes:
        st.info("No resumes yet. Upload your first one above!")
        return

    # Sort by created_at (most recent first)
    resumes.sort(key=lambda x: x.created_at, reverse=True)

    st.subheader(f"📋 Your Resumes ({len(resumes)})")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        show_master = st.checkbox("Show Master Only", value=False)

    with col2:
        show_tailored = st.checkbox("Show Tailored Only", value=False)

    with col3:
        show_active_only = st.checkbox("Show Active Only", value=False)

    # Apply filters
    filtered_resumes = resumes
    if show_master:
        filtered_resumes = [r for r in filtered_resumes if r.is_master]
    if show_tailored:
        filtered_resumes = [r for r in filtered_resumes if not r.is_master]
    if show_active_only:
        filtered_resumes = [r for r in filtered_resumes if r.is_active]

    if not filtered_resumes:
        st.info("No resumes match the selected filters.")
        return

    # Display resumes
    for resume in filtered_resumes:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.markdown(f"**{resume.get_status_emoji()} {resume.name}**")
                badges = f"v{resume.version}"
                if resume.is_master:
                    badges += " • Master"
                if resume.tailored_for_company:
                    badges += f" • {resume.tailored_for_company}"
                st.caption(badges)

            with col2:
                st.write(f"📁 {resume.file_type.upper() if resume.file_type else 'N/A'}")
                if resume.skills:
                    st.caption(f"Skills: {len(resume.skills)}")

            with col3:
                st.write(f"📊 {resume.applications_count} applications")
                if resume.success_rate > 0:
                    st.caption(f"Success: {resume.success_rate:.0f}%")

            with col4:
                if st.button("View", key=f"view_{resume.id}"):
                    st.session_state['view_resume_id'] = resume.id
                    st.rerun()

            st.divider()


def show_resume_detail(db: ResumeDB, resume_id: str):
    """Show detailed view of a resume"""
    resume = db.get_resume(resume_id)

    if not resume:
        st.error("Resume not found!")
        return

    # Header
    col1, col2 = st.columns([4, 1])

    with col1:
        st.title(f"{resume.get_status_emoji()} {resume.name}")
        st.caption(f"Version {resume.version} • Created {resume.created_at[:10]}")

    with col2:
        if st.button("← Back to List"):
            del st.session_state['view_resume_id']
            if 'edit_mode' in st.session_state:
                del st.session_state['edit_mode']
            st.rerun()

    st.divider()

    # Metadata tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Content", "ℹ️ Info", "📊 Analytics", "⚙️ Actions"])

    with tab1:
        st.subheader("Resume Content")

        # Download button
        col1, col2 = st.columns([1, 4])

        with col1:
            if resume.file_path and db.get_file_bytes(resume_id):
                # Original file exists - download original
                file_bytes = db.get_file_bytes(resume_id)
                st.download_button(
                    label="📥 Download Original",
                    data=file_bytes,
                    file_name=resume.original_filename or f"{resume.name}.{resume.file_type}",
                    mime=f"application/{resume.file_type}"
                )
            else:
                # No file - download as text (for tailored resumes)
                st.download_button(
                    label="📥 Download as Text",
                    data=resume.full_text.encode('utf-8'),
                    file_name=f"{resume.name}.txt",
                    mime="text/plain",
                    help="Download tailored resume content as text file"
                )

        with col2:
            if resume.original_filename:
                st.caption(f"Original file: {resume.original_filename}")
            elif not resume.is_master:
                st.caption("Tailored resume (text only)")

        if resume.skills:
            st.subheader("🔧 Detected Skills")
            st.write(", ".join(resume.skills))

    with tab2:
        st.subheader("Resume Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Status:**")
            st.write(f"- Master Resume: {'Yes' if resume.is_master else 'No'}")
            st.write(f"- Active: {'Yes' if resume.is_active else 'No'}")

            if resume.parent_id:
                st.write(f"- Parent Resume ID: {resume.parent_id}")

        with col2:
            st.write("**Details:**")
            st.write(f"- File Type: {resume.file_type.upper() if resume.file_type else 'N/A'}")
            st.write(f"- Skills: {len(resume.skills)} detected")
            st.write(f"- Last Used: {resume.last_used[:10] if resume.last_used else 'Never'}")

        if resume.tailored_for_company:
            st.write("**Tailoring:**")
            st.write(f"- Company: {resume.tailored_for_company}")
            if resume.tailored_for_job:
                st.write(f"- Job ID: {resume.tailored_for_job}")
            if resume.tailoring_notes:
                st.write(f"- Notes: {resume.tailoring_notes}")

    with tab3:
        st.subheader("Resume Analytics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Applications",
                resume.applications_count,
                help="Number of applications using this resume"
            )

        with col2:
            st.metric(
                "Success Rate",
                f"{resume.success_rate:.1f}%",
                help="Interview rate with this resume"
            )

        with col3:
            days_old = (datetime.now() - datetime.fromisoformat(resume.created_at)).days
            st.metric(
                "Age",
                f"{days_old} days",
                help="Days since resume was created"
            )

    with tab4:
        st.subheader("Resume Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✏️ Edit Resume", use_container_width=True):
                st.session_state['edit_mode'] = not st.session_state.get('edit_mode', False)
                st.rerun()

        with col2:
            if st.button("🎯 Tailor for Job", use_container_width=True):
                # Go back to main page and show tailor form
                del st.session_state['view_resume_id']
                st.session_state['show_tailor'] = True
                st.rerun()

        with col3:
            if not resume.is_active:
                if st.button("✅ Set as Active", use_container_width=True):
                    db.set_active_resume(resume_id)
                    st.success("Resume set as active!")
                    st.rerun()

        st.divider()

        # Edit form
        if st.session_state.get('edit_mode', False):
            st.markdown("### ✏️ Edit Resume")

            with st.expander("Edit Form", expanded=True):
                # Resume name
                new_name = st.text_input(
                    "Resume Name",
                    value=resume.name,
                    help="Descriptive name for this resume"
                )

                # Full text content
                new_full_text = st.text_area(
                    "Resume Content",
                    value=resume.full_text,
                    height=400,
                    help="Full text content of your resume"
                )

                # Skills (comma-separated)
                skills_str = ", ".join(resume.skills) if resume.skills else ""
                new_skills_str = st.text_input(
                    "Skills (comma-separated)",
                    value=skills_str,
                    help="List of skills, separated by commas"
                )

                # Status flags
                col1, col2 = st.columns(2)

                with col1:
                    new_is_master = st.checkbox(
                        "Master Resume",
                        value=resume.is_master,
                        help="Is this a master/template resume?"
                    )

                with col2:
                    new_is_active = st.checkbox(
                        "Active",
                        value=resume.is_active,
                        help="Is this resume currently active?"
                    )

                # Optional fields
                if not resume.is_master:
                    new_company = st.text_input(
                        "Tailored for Company",
                        value=resume.tailored_for_company or "",
                        help="Company this resume is tailored for"
                    )

                    new_tailoring_notes = st.text_area(
                        "Tailoring Notes",
                        value=resume.tailoring_notes or "",
                        height=100,
                        help="Notes about how this resume was tailored"
                    )

                # Action buttons
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("💾 Save Changes", type="primary", use_container_width=True):
                        # Update resume
                        resume.name = new_name
                        resume.full_text = new_full_text

                        # Parse skills
                        if new_skills_str.strip():
                            resume.skills = [s.strip() for s in new_skills_str.split(',') if s.strip()]
                        else:
                            resume.skills = []

                        resume.is_master = new_is_master
                        resume.is_active = new_is_active

                        if not resume.is_master:
                            resume.tailored_for_company = new_company
                            resume.tailoring_notes = new_tailoring_notes

                        # Update timestamp
                        resume.updated_at = datetime.now().isoformat()

                        # Save to database
                        db.update_resume(resume)

                        st.success("✅ Resume updated successfully!")
                        st.session_state['edit_mode'] = False
                        st.rerun()

                with col2:
                    if st.button("✕ Cancel", use_container_width=True):
                        st.session_state['edit_mode'] = False
                        st.rerun()

            st.divider()

        # Danger zone
        with st.expander("🗑️ Danger Zone"):
            st.warning("These actions cannot be undone!")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Deactivate Resume", type="secondary"):
                    resume.is_active = False
                    db.update_resume(resume)
                    st.success("Resume deactivated")
                    st.rerun()

            with col2:
                if st.button("Delete Resume", type="secondary"):
                    if st.session_state.get('confirm_delete'):
                        db.delete_resume(resume_id)
                        del st.session_state['view_resume_id']
                        st.success("Resume deleted!")
                        st.rerun()
                    else:
                        st.session_state['confirm_delete'] = True
                        st.warning("Click again to confirm deletion")


def main():
    st.set_page_config(page_title="Resume Management", page_icon="📄", layout="wide")

    st.title("📄 Resume Management")
    st.markdown("Upload, view, and manage your resumes")

    # Initialize database
    db = ResumeDB()

    # Get stats
    stats = db.get_stats()

    # Key Metrics
    st.header("📊 Resume Stats")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Resumes",
            stats['total_resumes'],
            help="All resumes in your library"
        )

    with col2:
        st.metric(
            "Master Resumes",
            stats['master_resumes'],
            help="Base template resumes"
        )

    with col3:
        st.metric(
            "Tailored Resumes",
            stats['tailored_resumes'],
            help="Job-specific versions"
        )

    with col4:
        st.metric(
            "Applications",
            stats['total_applications'],
            help="Total applications using these resumes"
        )

    st.divider()

    # Check if viewing detail
    if st.session_state.get('view_resume_id'):
        show_resume_detail(db, st.session_state['view_resume_id'])
        return

    # Quick Actions
    st.header("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Upload Resume", use_container_width=True):
            st.session_state['show_upload'] = True

    with col2:
        if st.button("📋 View All Resumes", use_container_width=True):
            st.session_state['show_upload'] = False

    with col3:
        if st.button("🎯 Tailor Resume", use_container_width=True):
            st.session_state['show_tailor'] = True
            st.session_state['show_upload'] = False

    st.divider()

    # Show upload form if requested
    if st.session_state.get('show_upload', False):
        show_upload_resume_form(db)

        if st.button("✕ Close Upload"):
            st.session_state['show_upload'] = False
            st.rerun()

        st.divider()

    # Show tailor form if requested
    if st.session_state.get('show_tailor', False):
        show_tailor_resume_form(db)

        if st.button("✕ Close Tailor Form"):
            st.session_state['show_tailor'] = False
            st.rerun()

        st.divider()

    # Show resume list
    show_resume_list(db)

    # Navigation
    st.divider()
    st.header("🧭 Navigation")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

    with col2:
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("pages/dashboard.py")

    with col3:
        if st.button("📝 Applications", use_container_width=True):
            st.switch_page("pages/applications.py")


if __name__ == "__main__":
    main()
