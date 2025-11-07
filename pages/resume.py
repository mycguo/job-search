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
from models.resume import create_resume, extract_skills_from_text
from PyPDF2 import PdfReader
import docx


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
            st.rerun()

    st.divider()

    # Metadata tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Content", "ℹ️ Info", "📊 Analytics", "⚙️ Actions"])

    with tab1:
        st.subheader("Resume Content")

        if resume.file_path and db.get_file_bytes(resume_id):
            file_bytes = db.get_file_bytes(resume_id)

            col1, col2 = st.columns([1, 4])

            with col1:
                st.download_button(
                    label="📥 Download",
                    data=file_bytes,
                    file_name=resume.original_filename or f"{resume.name}.{resume.file_type}",
                    mime=f"application/{resume.file_type}"
                )

            with col2:
                st.caption(f"Original file: {resume.original_filename}")

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
                st.info("Coming soon: Edit resume content")

        with col2:
            if st.button("🎯 Tailor for Job", use_container_width=True):
                st.info("Coming soon: AI-powered resume tailoring")

        with col3:
            if not resume.is_active:
                if st.button("✅ Set as Active", use_container_width=True):
                    db.set_active_resume(resume_id)
                    st.success("Resume set as active!")
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
            st.info("Coming soon: AI-powered resume tailoring!")

    st.divider()

    # Show upload form if requested
    if st.session_state.get('show_upload', False):
        show_upload_resume_form(db)

        if st.button("✕ Close Upload"):
            st.session_state['show_upload'] = False
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
