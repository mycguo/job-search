"""
Quick Notes - Grouped Table Layout

A grouped 2-column table for quick reference information.
Allows multiple entries per label (e.g., multiple referral codes, multiple phone numbers).
Opens in a separate tab for easy side-by-side viewing.
"""

import streamlit as st
import sys
from datetime import datetime
import pandas as pd
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, '.')

from storage.json_db import JobSearchDB
from storage.auth_utils import is_user_logged_in, login, logout


def login_screen():
    st.header("Please log in to access Quick Notes")
    st.subheader("Please log in.")
    st.button("Log in with Google", on_click=login)


def main():
    st.set_page_config(page_title="Quick Notes", page_icon="📝", layout="wide")

    # JavaScript to auto-open in new tab when clicked from navigation
    st.markdown("""
        <script>
            // Check if this is NOT already in a new tab/window
            if (!window.sessionStorage.getItem('quick_notes_new_tab')) {
                // Check if this is the first load (from navigation click)
                if (!window.opener && window.history.length <= 2) {
                    // Mark that we're opening in a new tab
                    window.sessionStorage.setItem('quick_notes_new_tab', 'true');
                    // Open in new tab
                    window.open(window.location.href, '_blank');
                    // Go back in the main window
                    window.history.back();
                }
            }
        </script>
    """, unsafe_allow_html=True)

    if not is_user_logged_in():
        login_screen()
        return

    # Header with compact layout
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("📝 Quick Notes")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col3:
        if st.button("📥 Export CSV", use_container_width=True):
            st.session_state['show_export'] = not st.session_state.get('show_export', False)

    # Initialize database
    db = JobSearchDB()

    # Get existing notes
    notes = db.get_quick_notes()

    # Display notes grouped by label - MOVED TO TOP FOR QUICK REFERENCE
    if notes:
        # Group notes by label
        grouped_notes = defaultdict(list)
        for note in notes:
            grouped_notes[note['label']].append(note)

        st.markdown("### 📋 Quick Reference")
        st.caption(f"{len(notes)} items · {len(grouped_notes)} categories")

        # Display each category - compact with inline category labels
        for label, label_notes in sorted(grouped_notes.items()):
            # Check if this category is being edited
            category_key = f"edit_category_{label}"
            is_editing_category = st.session_state.get(category_key, False)

            # Edit mode for this category
            if is_editing_category:
                # Show compact header when editing
                col1, col2 = st.columns([6, 0.5])
                with col1:
                    st.markdown(f"**✏️ Editing: {label}**")
                with col2:
                    pass
                with st.container():
                    with st.form(f"edit_category_form_{label}"):
                        # Category name (can be changed to move all items to different category)
                        new_category_name = st.text_input("Category Name", value=label, key=f"cat_name_{label}")

                        st.markdown("**Existing Content Entries:**")

                        # Show all existing entries with ability to edit or delete
                        entries_to_update = []
                        entries_to_delete = []

                        for idx, note in enumerate(label_notes):
                            note_id = note['id']
                            content = note['content']

                            col1, col2 = st.columns([5, 1])
                            with col1:
                                edited_content = st.text_input(
                                    f"Entry {idx+1}",
                                    value=content,
                                    key=f"edit_cat_content_{note_id}",
                                    label_visibility="collapsed"
                                )
                                entries_to_update.append({'id': note_id, 'content': edited_content})

                            with col2:
                                # Delete checkbox for this entry
                                delete_entry = st.checkbox("🗑️", key=f"delete_entry_{note_id}", label_visibility="collapsed")
                                if delete_entry:
                                    entries_to_delete.append(note_id)

                        # Add new content rows
                        st.markdown("**Add More Entries:**")
                        if f'edit_add_count_{label}' not in st.session_state:
                            st.session_state[f'edit_add_count_{label}'] = 0

                        new_contents = []
                        for i in range(st.session_state[f'edit_add_count_{label}']):
                            new_content = st.text_input(
                                f"New {i+1}",
                                placeholder="New content entry...",
                                key=f"new_content_{label}_{i}",
                                label_visibility="collapsed"
                            )
                            if new_content.strip():
                                new_contents.append(new_content)

                        # Buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.form_submit_button("➕ Add Row"):
                                st.session_state[f'edit_add_count_{label}'] += 1
                                st.rerun()

                        with col2:
                            if st.form_submit_button("💾 Save", type="primary"):
                                # Update existing entries
                                for entry in entries_to_update:
                                    if entry['id'] not in entries_to_delete and entry['content'].strip():
                                        db.update_quick_note(entry['id'], new_category_name, entry['content'], note_type="text")

                                # Delete marked entries
                                for note_id in entries_to_delete:
                                    db.delete_quick_note(note_id)

                                # Add new entries
                                for new_content in new_contents:
                                    db.add_quick_note(new_category_name, new_content, note_type="text")

                                # Reset state
                                st.session_state[category_key] = False
                                st.session_state[f'edit_add_count_{label}'] = 0
                                st.success(f"✅ Updated category '{label}'")
                                st.rerun()

                        with col3:
                            if st.form_submit_button("✕ Cancel"):
                                st.session_state[category_key] = False
                                st.session_state[f'edit_add_count_{label}'] = 0
                                st.rerun()

            # Display mode - show category and content on one line
            else:
                for idx, note in enumerate(label_notes):
                    note_id = note['id']
                    content = note['content']

                    col1, col2, col3 = st.columns([1.5, 4.5, 0.5])

                    with col1:
                        # Category label - show edit button only on first item
                        if idx == 0:
                            if st.button(f"📌 {label}", key=f"cat_label_{label}", use_container_width=True, help="Click to edit"):
                                st.session_state[category_key] = True
                                st.rerun()
                        else:
                            st.markdown(f"**📌 {label}**")

                    with col2:
                        # Copyable content
                        st.text_input(
                            "C",
                            value=content,
                            key=f"content_{note_id}",
                            label_visibility="collapsed"
                        )

                    with col3:
                        # Quick delete button
                        if st.button("🗑️", key=f"delete_btn_{note_id}", use_container_width=True):
                            db.delete_quick_note(note_id)
                            st.rerun()

    # Compact add form in expander with multiple content rows - MOVED TO BOTTOM
    st.markdown("---")
    with st.expander("➕ Add New Category", expanded=False):
        # Initialize number of content rows in session state
        if 'add_content_count' not in st.session_state:
            st.session_state['add_content_count'] = 1

        with st.form("add_note_form", clear_on_submit=False):
            # Get existing labels for autocomplete suggestions
            existing_labels = sorted(list(set([note['label'] for note in notes]))) if notes else []

            new_label = st.text_input(
                "Category Name",
                placeholder="e.g., Referral Codes, Phone Numbers, LinkedIn",
            )
            if existing_labels:
                st.caption(f"📌 Existing: {', '.join(existing_labels[:5])}")

            st.markdown("**Content Entries:**")

            # Display content input rows
            content_values = []
            for i in range(st.session_state['add_content_count']):
                col1, col2 = st.columns([5, 1])
                with col1:
                    content_val = st.text_input(
                        f"Content {i+1}",
                        placeholder=f"e.g., Company A: REF123 or https://linkedin.com/in/...",
                        key=f"add_content_{i}",
                        label_visibility="collapsed"
                    )
                    content_values.append(content_val)
                with col2:
                    # Only show remove button if more than 1 row
                    if st.session_state['add_content_count'] > 1:
                        if st.form_submit_button("✕", key=f"remove_add_{i}"):
                            st.session_state['add_content_count'] -= 1
                            st.rerun()

            # Add row button and Submit
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("➕ Add Another Row"):
                    st.session_state['add_content_count'] += 1
                    st.rerun()

            with col2:
                submit = st.form_submit_button("💾 Save All", type="primary", use_container_width=True)

            if submit:
                if not new_label:
                    st.error("Please enter a category name")
                else:
                    # Filter out empty content entries
                    valid_contents = [c for c in content_values if c.strip()]

                    if not valid_contents:
                        st.error("Please enter at least one content entry")
                    else:
                        # Add all content entries
                        for content in valid_contents:
                            db.add_quick_note(new_label, content, note_type="text")

                        st.success(f"✅ Added {len(valid_contents)} items to '{new_label}'")
                        # Reset form
                        st.session_state['add_content_count'] = 1
                        st.rerun()

    # Show example if no notes
    if not notes:
        with st.expander("💡 Example entries"):
            st.markdown("""
            **LinkedIn**
            - https://linkedin.com/in/yourprofile
            - https://linkedin.com/company/target

            **Referral Codes**
            - Company A: REF123
            - Company B: REF456

            **Phone Numbers**
            - (555) 123-4567
            - (555) 987-6543
            """)

    # Export section - only show if button clicked
    if st.session_state.get('show_export', False) and notes:
        with st.container():
            df = pd.DataFrame([{'Label': n['label'], 'Content': n['content']} for n in notes])
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="quick_notes.csv",
                mime="text/csv",
                use_container_width=True
            )
            if st.button("✕ Close", use_container_width=True):
                st.session_state['show_export'] = False
                st.rerun()


if __name__ == "__main__":
    main()
