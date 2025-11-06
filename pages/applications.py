"""
Application Management Page

Manage all job applications in one place.
"""

import streamlit as st
import sys
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, '.')

from models.application import Application, create_application
from storage.json_db import JobSearchDB
from ai.job_matcher import JobMatcher, get_default_user_profile


def show_application_card(app: Application, db: JobSearchDB):
    """Display an application as a card with actions"""

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

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
            # Action buttons
            with st.popover("⚙️ Actions"):
                # Status update
                new_status = st.selectbox(
                    "Update Status",
                    ["applied", "screening", "interview", "offer", "accepted", "rejected", "withdrawn"],
                    index=["applied", "screening", "interview", "offer", "accepted", "rejected", "withdrawn"].index(app.status),
                    key=f"status_{app.id}"
                )

                status_note = st.text_input("Note (optional)", key=f"note_{app.id}")

                if st.button("Update Status", key=f"update_btn_{app.id}"):
                    if new_status != app.status:
                        db.update_status(app.id, new_status, status_note or None)
                        st.success(f"✅ Status updated to {new_status}")
                        st.rerun()

                st.divider()

                # Delete option
                if st.button("🗑️ Delete", key=f"delete_{app.id}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{app.id}", False):
                        db.delete_application(app.id)
                        st.success("Deleted!")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{app.id}"] = True
                        st.warning("Click again to confirm deletion")

        # Expandable details
        with st.expander("📋 Details & AI Analysis"):
            # Basic info
            if app.salary_range:
                st.write(f"**Salary:** {app.salary_range}")

            if app.job_url:
                st.write(f"**Job URL:** [{app.job_url}]({app.job_url})")

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
                st.text_area("", value=app.notes, height=100, disabled=True, key=f"notes_view_{app.id}")

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


def main():
    st.set_page_config(page_title="Applications", page_icon="📝", layout="wide")

    st.title("📝 Job Applications")
    st.markdown("Manage all your job applications in one place")

    # Initialize database
    db = JobSearchDB()

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
                            match_score=match_score
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


if __name__ == "__main__":
    main()
