"""
Application Management Page

Manage all job applications in one place.
"""

import streamlit as st
import sys
from datetime import datetime
import json
from typing import Optional

# Add parent directory to path
sys.path.insert(0, '.')

from models.application import Application, ContactLink, create_application


def build_contact_link(name: str, url: str) -> Optional[ContactLink]:
    """Create a ContactLink object when data is provided"""
    sanitized_name = (name or "").strip()
    sanitized_url = (url or "").strip()

    if not sanitized_name and not sanitized_url:
        return None

    return ContactLink(
        name=sanitized_name or None,
        url=sanitized_url or None
    )


def render_contact(label: str, contact: Optional[ContactLink]):
    """Display a contact link if available"""
    if not contact:
        return

    display_name = contact.name or label

    if contact.url:
        st.markdown(f"**{label}:** [{display_name}]({contact.url})")
    else:
        st.write(f"**{label}:** {display_name}")

from storage.json_db import JobSearchDB
from ai.job_matcher import JobMatcher, get_default_user_profile


def show_application_card(app: Application, db: JobSearchDB):
    """Display an application as a card with actions"""

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"### {app.get_status_emoji()} **{app.company}**")
            st.markdown(f"**{app.role}**")
            if app.location:
                st.caption(f"📍 {app.location}")

        with col2:
            st.write("**Applied**")
            st.write(app.applied_date)
            days = app.get_days_since_applied()
            if days > 0:
                st.caption(f"({days} days ago)")

        with col3:
            st.write("**Status**")
            status_colors = {
                "applied": "🔵",
                "screening": "🟡",
                "interview": "🟠",
                "offer": "🟢",
                "accepted": "✅",
                "rejected": "🔴",
                "withdrawn": "⚫"
            }
            st.markdown(f"{status_colors.get(app.status, '⚪')} {app.get_display_status()}")

        with col4:
            if st.button("View", key=f"view_{app.id}"):
                st.session_state['view_application_id'] = app.id
                st.rerun()

        # Expandable details
        with st.expander("📋 Details & AI Analysis"):
            # Basic info
            if app.salary_range:
                st.write(f"**Salary:** {app.salary_range}")

            if app.job_url:
                st.write(f"**Job URL:** [{app.job_url}]({app.job_url})")

            if app.recruiter_contact or app.hiring_manager_contact:
                st.write("**👥 Contacts:**")
                render_contact("Recruiter", app.recruiter_contact)
                render_contact("Hiring Manager", app.hiring_manager_contact)

            # Match score
            if app.match_score and app.match_score > 0:
                st.write(f"**Match Score:** {app.match_score * 100:.0f}%")
                st.progress(app.match_score)

                # Color-coded recommendation
                score_pct = app.match_score * 100
                if score_pct >= 80:
                    st.success("🎯 Excellent match!")
                elif score_pct >= 60:
                    st.info("👍 Good match")
                else:
                    st.warning("⚠️ Moderate match")

            # Job requirements (if analyzed)
            if app.job_requirements:
                st.divider()
                st.write("**🤖 AI-Extracted Requirements:**")

                reqs = app.job_requirements

                col1, col2 = st.columns(2)
                with col1:
                    if reqs.get("required_skills"):
                        st.write("**Required Skills:**")
                        for skill in reqs["required_skills"][:5]:
                            st.write(f"• {skill}")

                    if reqs.get("years_experience"):
                        st.write(f"**Experience:** {reqs['years_experience']}")

                with col2:
                    if reqs.get("preferred_skills"):
                        st.write("**Preferred Skills:**")
                        for skill in reqs["preferred_skills"][:5]:
                            st.write(f"• {skill}")

                    if reqs.get("role_level"):
                        st.write(f"**Level:** {reqs['role_level']}")

            # Generate cover letter button
            if app.job_description:
                st.divider()
                if st.button("✍️ Generate Cover Letter", key=f"coverletter_{app.id}"):
                    with st.spinner("Generating cover letter..."):
                        try:
                            matcher = JobMatcher()
                            profile = get_default_user_profile()

                            cover_letter = matcher.generate_cover_letter(
                                company=app.company,
                                role=app.role,
                                job_requirements=app.job_requirements or {},
                                user_profile=profile,
                                job_description=app.job_description
                            )

                            st.text_area("Cover Letter:", value=cover_letter, height=300)
                            st.success("✅ Cover letter generated! Copy and customize as needed.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            st.caption("Note: Requires valid Google API key")

            if app.notes:
                st.write("**Notes:**")
                st.text_area(
                    "Application notes",
                    value=app.notes,
                    height=100,
                    disabled=True,
                    key=f"notes_view_{app.id}",
                    label_visibility="collapsed"
                )

            # Timeline
            if len(app.timeline) > 0:
                st.write("**Timeline:**")
                for event in app.timeline:
                    st.write(f"- {event.date}: {event.event_type.title()}")
                    if event.notes:
                        st.caption(f"  {event.notes}")

            # Add note button
            st.divider()
            new_note = st.text_input("Add a note:", key=f"add_note_{app.id}")
            if st.button("Add Note", key=f"add_note_btn_{app.id}"):
                if new_note:
                    db.add_application_note(app.id, new_note)
                    st.success("Note added!")
                    st.rerun()

        st.divider()


def show_application_detail(db: JobSearchDB, app_id: str):
    """Show detailed view of an application with edit capability"""
    app = db.get_application(app_id)

    if not app:
        st.error("Application not found!")
        return

    # Header
    col1, col2 = st.columns([4, 1])

    with col1:
        st.title(f"{app.get_status_emoji()} {app.company} - {app.role}")
        st.caption(f"Applied on {app.applied_date} • Status: {app.get_display_status()}")

    with col2:
        if st.button("← Back to List"):
            del st.session_state['view_application_id']
            st.rerun()

    st.divider()

    # Tabs for organization
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Details", "📊 Analysis", "📅 Timeline", "✏️ Edit Application"])

    with tab1:
        st.subheader("Application Details")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Basic Information:**")
            st.write(f"• Company: {app.company}")
            st.write(f"• Role: {app.role}")
            st.write(f"• Location: {app.location or 'Not specified'}")
            st.write(f"• Applied: {app.applied_date}")
            if app.salary_range:
                st.write(f"• Salary Range: {app.salary_range}")

        with col2:
            st.write("**Links & Resources:**")
            if app.job_url:
                st.markdown(f"• [Job Posting]({app.job_url})")
            else:
                st.write("• No job URL provided")

            days_ago = app.get_days_since_applied()
            st.write(f"• Days since applied: {days_ago}")

            if app.recruiter_contact or app.hiring_manager_contact:
                st.write("**Key Contacts:**")
                render_contact("Recruiter", app.recruiter_contact)
                render_contact("Hiring Manager", app.hiring_manager_contact)

        if app.job_description:
            st.divider()
            st.subheader("Job Description")
            with st.expander("View full job description"):
                st.text_area(
                    "Description",
                    value=app.job_description,
                    height=300,
                    disabled=True,
                    key=f"job_desc_view_{app.id}"
                )

        if app.notes:
            st.divider()
            st.subheader("Notes")
            st.text_area(
                "Your notes",
                value=app.notes,
                height=150,
                disabled=True,
                key=f"notes_view_{app.id}"
            )

    with tab2:
        st.subheader("AI Analysis & Match Score")

        if app.match_score and app.match_score > 0:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Match Score",
                    f"{app.match_score * 100:.0f}%",
                    help="AI-calculated match score"
                )

            with col2:
                score_pct = app.match_score * 100
                if score_pct >= 80:
                    st.success("🎯 Excellent match!")
                elif score_pct >= 60:
                    st.info("👍 Good match")
                else:
                    st.warning("⚠️ Moderate match")

            with col3:
                st.metric("Days Active", app.get_days_since_applied())

            st.divider()
            st.progress(app.match_score)
        else:
            st.info("No AI analysis available for this application")

        # Job requirements
        if app.job_requirements:
            st.divider()
            st.subheader("Extracted Requirements")

            reqs = app.job_requirements

            col1, col2 = st.columns(2)

            with col1:
                if reqs.get("required_skills"):
                    st.write("**Required Skills:**")
                    for skill in reqs["required_skills"]:
                        st.write(f"• {skill}")

                if reqs.get("years_experience"):
                    st.write(f"**Experience Required:** {reqs['years_experience']}")

            with col2:
                if reqs.get("preferred_skills"):
                    st.write("**Preferred Skills:**")
                    for skill in reqs["preferred_skills"]:
                        st.write(f"• {skill}")

                if reqs.get("role_level"):
                    st.write(f"**Level:** {reqs['role_level']}")

        # Generate cover letter
        if app.job_description:
            st.divider()
            if st.button("✍️ Generate Cover Letter", use_container_width=True):
                with st.spinner("Generating cover letter..."):
                    try:
                        matcher = JobMatcher()
                        profile = get_default_user_profile()

                        cover_letter = matcher.generate_cover_letter(
                            company=app.company,
                            role=app.role,
                            job_requirements=app.job_requirements or {},
                            user_profile=profile,
                            job_description=app.job_description
                        )

                        st.text_area("Cover Letter:", value=cover_letter, height=400)
                        st.success("✅ Cover letter generated!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with tab3:
        st.subheader("Application Timeline")

        if app.timeline:
            for event in app.timeline:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"**{event.date}**")
                with col2:
                    st.write(f"{event.event_type.title()}")
                    if event.notes:
                        st.caption(event.notes)
                st.divider()
        else:
            st.info("No timeline events yet")

        # Add event
        st.subheader("Add Timeline Event")
        with st.form(f"add_event_{app.id}"):
            col1, col2 = st.columns(2)
            with col1:
                event_type = st.selectbox(
                    "Event Type",
                    ["screening", "interview", "offer", "rejected", "withdrawn", "follow_up", "other"]
                )
            with col2:
                event_date = st.date_input("Event Date", value=datetime.now())

            event_notes = st.text_area("Notes", placeholder="Add details about this event...")

            if st.form_submit_button("Add Event"):
                # Add timeline event with the specified date
                event_date_str = event_date.strftime("%Y-%m-%d")
                success = db.add_timeline_event(app.id, event_type, event_date_str, event_notes)
                
                if success:
                    st.success("✅ Event added to timeline!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add event. Please try again.")

    with tab4:
        # Edit form - shown directly
        st.markdown("### ✏️ Edit Application Details")

        with st.expander("Edit Form", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                new_company = st.text_input("Company", value=app.company)
                new_role = st.text_input("Role", value=app.role)
                new_location = st.text_input("Location", value=app.location or "")

            with col2:
                new_status = st.selectbox(
                    "Status",
                    ["applied", "screening", "interview", "offer", "accepted", "rejected", "withdrawn"],
                    index=["applied", "screening", "interview", "offer", "accepted", "rejected", "withdrawn"].index(app.status)
                )
                new_applied_date = st.date_input(
                    "Applied Date",
                    value=datetime.strptime(app.applied_date, "%Y-%m-%d")
                )
                new_salary_range = st.text_input("Salary Range", value=app.salary_range or "")

            new_job_url = st.text_input("Job URL", value=app.job_url or "")

            new_job_description = st.text_area(
                "Job Description",
                value=app.job_description or "",
                height=200
            )

            new_notes = st.text_area(
                "Notes",
                value=app.notes or "",
                height=150
            )

            st.markdown("**Key Contacts**")
            edit_contact_col1, edit_contact_col2 = st.columns(2)

            with edit_contact_col1:
                recruiter_name_value = st.text_input(
                    "Recruiter Name",
                    value=app.recruiter_contact.name if app.recruiter_contact and app.recruiter_contact.name else "",
                    key=f"edit_recruiter_name_{app.id}"
                )
                recruiter_link_value = st.text_input(
                    "Recruiter Contact Link",
                    value=app.recruiter_contact.url if app.recruiter_contact and app.recruiter_contact.url else "",
                    key=f"edit_recruiter_link_{app.id}"
                )

            with edit_contact_col2:
                hiring_manager_name_value = st.text_input(
                    "Hiring Manager Name",
                    value=app.hiring_manager_contact.name if app.hiring_manager_contact and app.hiring_manager_contact.name else "",
                    key=f"edit_hiring_manager_name_{app.id}"
                )
                hiring_manager_link_value = st.text_input(
                    "Hiring Manager Contact Link",
                    value=app.hiring_manager_contact.url if app.hiring_manager_contact and app.hiring_manager_contact.url else "",
                    key=f"edit_hiring_manager_link_{app.id}"
                )

            # Action buttons
            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Save Changes", type="primary", use_container_width=True):
                    # Prepare updates
                    updates = {
                        'company': new_company,
                        'role': new_role,
                        'location': new_location if new_location else None,
                        'status': new_status,
                        'applied_date': new_applied_date.strftime("%Y-%m-%d"),
                        'salary_range': new_salary_range if new_salary_range else None,
                        'job_url': new_job_url if new_job_url else None,
                        'job_description': new_job_description if new_job_description else None,
                        'notes': new_notes if new_notes else None,
                        'recruiter_contact': build_contact_link(recruiter_name_value, recruiter_link_value),
                        'hiring_manager_contact': build_contact_link(hiring_manager_name_value, hiring_manager_link_value)
                    }

                    # Update in database
                    db.update_application(app_id, updates)

                    st.success("✅ Application updated successfully!")
                    st.rerun()

            with col2:
                if st.button("✕ Cancel", use_container_width=True):
                    st.rerun()

        st.divider()

        # Danger zone
        with st.expander("🗑️ Danger Zone"):
            st.warning("These actions cannot be undone!")

            if st.button("Delete Application", type="secondary"):
                if st.session_state.get('confirm_delete_detail'):
                    db.delete_application(app_id)
                    del st.session_state['view_application_id']
                    st.success("Application deleted!")
                    st.rerun()
                else:
                    st.session_state['confirm_delete_detail'] = True
                    st.warning("Click again to confirm deletion")


def login_screen():
    st.header("Please log in to access Applications")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=st.login)


def main():
    st.set_page_config(page_title="Applications", page_icon="📝", layout="wide")

    if not st.user.is_logged_in:
        login_screen()
        return

    st.title("📝 Job Applications")
    st.markdown("Manage all your job applications in one place")

    # Initialize database
    db = JobSearchDB()

    # Check if viewing detail
    if st.session_state.get('view_application_id'):
        show_application_detail(db, st.session_state['view_application_id'])
        return

    # Sidebar filters and stats
    with st.sidebar:
        st.header("📊 Quick Stats")

        stats = db.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", stats['total'])
            st.metric("Active", stats['active'])
        with col2:
            st.metric("Response Rate", f"{stats['response_rate']}%")

        st.divider()

        # Filters
        st.header("🔍 Filters")

        status_filter = st.selectbox(
            "Status",
            ["All", "Applied", "Screening", "Interview", "Offer", "Accepted", "Rejected", "Withdrawn"]
        )

        company_search = st.text_input("Search Company", placeholder="e.g., Google")

        sort_by = st.selectbox(
            "Sort By",
            ["Applied Date (Newest)", "Applied Date (Oldest)", "Company (A-Z)", "Company (Z-A)"]
        )

    # Add new application
    st.header("➕ Add New Application")

    with st.expander("Click to add a new application", expanded=False):
        with st.form("new_application", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                company = st.text_input("Company *", placeholder="e.g., Google")
                role = st.text_input("Role *", placeholder="e.g., Senior ML Engineer")
                location = st.text_input("Location", placeholder="e.g., San Francisco, CA or Remote")

            with col2:
                status = st.selectbox(
                    "Status",
                    ["applied", "screening", "interview", "offer"]
                )
                applied_date = st.date_input("Applied Date", value=datetime.now())
                salary_range = st.text_input("Salary Range", placeholder="e.g., $150k-$200k")

            job_url = st.text_input("Job URL", placeholder="https://...")
            job_description = st.text_area("Job Description (optional)", height=150,
                                          placeholder="Paste job description here for AI analysis...")

            st.markdown("**Key Contacts (optional)**")
            contact_col1, contact_col2 = st.columns(2)
            with contact_col1:
                recruiter_name = st.text_input(
                    "Recruiter Name",
                    placeholder="e.g., Jane Recruiter",
                    key="new_recruiter_name"
                )
                recruiter_link = st.text_input(
                    "Recruiter Contact Link",
                    placeholder="https://linkedin.com/in/...",
                    key="new_recruiter_link"
                )
            with contact_col2:
                hiring_manager_name = st.text_input(
                    "Hiring Manager Name",
                    placeholder="e.g., Alex Hiring",
                    key="new_hiring_manager_name"
                )
                hiring_manager_link = st.text_input(
                    "Hiring Manager Contact Link",
                    placeholder="https://linkedin.com/in/...",
                    key="new_hiring_manager_link"
                )

            # AI Analysis button
            analyze_job = st.checkbox("🤖 Analyze job with AI", value=False,
                                     help="Use AI to extract requirements and calculate match score")

            notes = st.text_area("Notes (optional)", height=80,
                                placeholder="e.g., Referred by John, team focuses on AI/ML...")

            submit = st.form_submit_button("Add Application", type="primary")

            if submit:
                if not company or not role:
                    st.error("⚠️ Company and Role are required!")
                else:
                    try:
                        # Analyze job if requested
                        job_requirements = None
                        match_score = None

                        if analyze_job and job_description:
                            with st.spinner("🤖 Analyzing job description with AI..."):
                                try:
                                    matcher = JobMatcher()

                                    # Extract requirements
                                    job_requirements = matcher.extract_requirements(job_description)
                                    st.success("✅ Job requirements extracted!")

                                    # Calculate match score
                                    user_profile = get_default_user_profile()
                                    match_analysis = matcher.calculate_match_score(
                                        job_requirements,
                                        user_profile
                                    )

                                    match_score = match_analysis.get("match_score", 0)
                                    overall_score = match_analysis.get("overall_score", 0)

                                    # Show analysis
                                    st.info(f"📊 Match Score: {overall_score}/100")

                                    with st.expander("📋 View Analysis"):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write("**Matching Skills:**")
                                            for skill in match_analysis.get("matching_skills", [])[:5]:
                                                st.write(f"✅ {skill}")
                                        with col2:
                                            st.write("**Missing Skills:**")
                                            for skill in match_analysis.get("missing_skills", [])[:5]:
                                                st.write(f"⚠️ {skill}")

                                        st.write("**Recommendation:**",
                                                match_analysis.get("recommendation", "Review manually"))

                                except Exception as e:
                                    st.warning(f"⚠️ AI analysis failed: {str(e)}")
                                    st.caption("Continuing without AI analysis...")

                        # Create application
                        recruiter_contact = build_contact_link(recruiter_name, recruiter_link)
                        hiring_manager_contact = build_contact_link(hiring_manager_name, hiring_manager_link)

                        app = create_application(
                            company=company,
                            role=role,
                            status=status,
                            applied_date=applied_date.strftime("%Y-%m-%d"),
                            location=location or None,
                            salary_range=salary_range or None,
                            job_url=job_url or None,
                            job_description=job_description or None,
                            notes=notes or None,
                            job_requirements=job_requirements,
                            match_score=match_score,
                            recruiter_contact=recruiter_contact,
                            hiring_manager_contact=hiring_manager_contact
                        )

                        db.add_application(app)
                        st.success(f"✅ Added application to {company}!")
                        st.balloons()
                        st.rerun()

                    except ValueError as e:
                        st.error(f"⚠️ {str(e)}")

    # List applications
    st.header("📋 Your Applications")

    # Apply filters
    status_map = {
        "All": None,
        "Applied": "applied",
        "Screening": "screening",
        "Interview": "interview",
        "Offer": "offer",
        "Accepted": "accepted",
        "Rejected": "rejected",
        "Withdrawn": "withdrawn"
    }

    filtered_status = status_map.get(status_filter)

    # Get applications
    applications = db.list_applications(status=filtered_status)

    # Apply company search
    if company_search:
        applications = [app for app in applications
                       if company_search.lower() in app.company.lower()]

    # Apply sorting
    if "Newest" in sort_by:
        applications = sorted(applications, key=lambda x: x.applied_date, reverse=True)
    elif "Oldest" in sort_by:
        applications = sorted(applications, key=lambda x: x.applied_date, reverse=False)
    elif "A-Z" in sort_by:
        applications = sorted(applications, key=lambda x: x.company.lower())
    elif "Z-A" in sort_by:
        applications = sorted(applications, key=lambda x: x.company.lower(), reverse=True)

    # Display count
    st.write(f"**Showing {len(applications)} application(s)**")

    if len(applications) == 0:
        st.info("🎯 No applications yet. Add your first one above!")
    else:
        # Display applications
        for app in applications:
            show_application_card(app, db)

    # Bulk actions
    if len(applications) > 0:
        st.divider()
        with st.expander("⚡ Bulk Actions"):
            st.write("Coming soon: Export to CSV, Bulk status update, etc.")
    
    # Logout button
    st.divider()
    st.button("Log out", on_click=st.logout)


if __name__ == "__main__":
    main()
