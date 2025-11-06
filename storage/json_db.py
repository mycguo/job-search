"""
JSON-based database for job search data.

Simple file-based storage using JSON for quick prototyping.
Can be upgraded to SQLite or PostgreSQL later.
"""

import json
import os
from typing import List, Optional, Dict, Callable
from datetime import datetime
from models.application import Application


class JobSearchDB:
    """Simple JSON database for job search data"""

    def __init__(self, data_dir: str = "./job_search_data"):
        """
        Initialize database.

        Args:
            data_dir: Directory to store JSON files
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.applications_file = os.path.join(data_dir, "applications.json")
        self.contacts_file = os.path.join(data_dir, "contacts.json")
        self.profile_file = os.path.join(data_dir, "profile.json")

        # Initialize files if they don't exist
        self._init_file(self.applications_file, [])
        self._init_file(self.contacts_file, [])
        self._init_file(self.profile_file, {})

    def _init_file(self, filepath: str, default_content):
        """Create file with default content if it doesn't exist"""
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump(default_content, f, indent=2)

    def _read_json(self, filepath: str):
        """Read JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading {filepath}: {e}")
            return [] if filepath != self.profile_file else {}

    def _write_json(self, filepath: str, data):
        """Write JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            raise

    # ==================== APPLICATION CRUD ====================

    def add_application(self, app: Application) -> str:
        """
        Add new application.

        Args:
            app: Application instance

        Returns:
            Application ID
        """
        applications = self._read_json(self.applications_file)

        # Check for duplicate
        for existing in applications:
            if (existing['company'].lower() == app.company.lower() and
                existing['role'].lower() == app.role.lower() and
                existing.get('status') not in ['rejected', 'withdrawn', 'accepted']):
                raise ValueError(f"Active application already exists for {app.company} - {app.role}")

        applications.append(app.to_dict())
        self._write_json(self.applications_file, applications)

        print(f"✅ Added application: {app.company} - {app.role} (ID: {app.id})")
        return app.id

    def get_application(self, app_id: str) -> Optional[Application]:
        """
        Get application by ID.

        Args:
            app_id: Application ID

        Returns:
            Application instance or None
        """
        applications = self._read_json(self.applications_file)

        for app_dict in applications:
            if app_dict['id'] == app_id:
                return Application.from_dict(app_dict)

        return None

    def list_applications(
        self,
        status: Optional[str] = None,
        company: Optional[str] = None,
        sort_by: str = "applied_date",
        reverse: bool = True
    ) -> List[Application]:
        """
        List applications with optional filtering.

        Args:
            status: Filter by status (e.g., 'applied', 'interview')
            company: Filter by company name (partial match)
            sort_by: Field to sort by (default: applied_date)
            reverse: Sort in reverse order (default: True - newest first)

        Returns:
            List of Application instances
        """
        applications = self._read_json(self.applications_file)
        results = []

        for app_dict in applications:
            app = Application.from_dict(app_dict)

            # Apply filters
            if status and app.status != status.lower():
                continue

            if company and company.lower() not in app.company.lower():
                continue

            results.append(app)

        # Sort
        if sort_by == "applied_date":
            results.sort(key=lambda x: x.applied_date, reverse=reverse)
        elif sort_by == "company":
            results.sort(key=lambda x: x.company.lower(), reverse=reverse)
        elif sort_by == "updated_at":
            results.sort(key=lambda x: x.updated_at, reverse=reverse)

        return results

    def update_application(self, app_id: str, updates: Dict) -> bool:
        """
        Update application fields.

        Args:
            app_id: Application ID
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        applications = self._read_json(self.applications_file)

        for i, app_dict in enumerate(applications):
            if app_dict['id'] == app_id:
                # Update fields
                app = Application.from_dict(app_dict)

                for key, value in updates.items():
                    if hasattr(app, key):
                        setattr(app, key, value)

                app.updated_at = datetime.now().isoformat()

                applications[i] = app.to_dict()
                self._write_json(self.applications_file, applications)

                print(f"✅ Updated application: {app.company} - {app.role}")
                return True

        print(f"❌ Application not found: {app_id}")
        return False

    def update_status(self, app_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        """
        Update application status and add timeline event.

        Args:
            app_id: Application ID
            new_status: New status
            notes: Optional notes

        Returns:
            True if successful
        """
        applications = self._read_json(self.applications_file)

        for i, app_dict in enumerate(applications):
            if app_dict['id'] == app_id:
                app = Application.from_dict(app_dict)
                old_status = app.status
                app.update_status(new_status, notes)

                applications[i] = app.to_dict()
                self._write_json(self.applications_file, applications)

                print(f"✅ Status updated: {app.company} - {old_status} → {new_status}")
                return True

        print(f"❌ Application not found: {app_id}")
        return False

    def delete_application(self, app_id: str) -> bool:
        """
        Delete application.

        Args:
            app_id: Application ID

        Returns:
            True if successful
        """
        applications = self._read_json(self.applications_file)
        original_length = len(applications)

        applications = [app for app in applications if app['id'] != app_id]

        if len(applications) < original_length:
            self._write_json(self.applications_file, applications)
            print(f"✅ Deleted application: {app_id}")
            return True

        print(f"❌ Application not found: {app_id}")
        return False

    def add_application_note(self, app_id: str, note: str) -> bool:
        """
        Add note to application.

        Args:
            app_id: Application ID
            note: Note text

        Returns:
            True if successful
        """
        app = self.get_application(app_id)
        if not app:
            return False

        current_notes = app.notes or ""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_note = f"[{timestamp}] {note}"

        if current_notes:
            app.notes = f"{current_notes}\n{new_note}"
        else:
            app.notes = new_note

        return self.update_application(app_id, {"notes": app.notes})

    # ==================== STATISTICS ====================

    def get_stats(self) -> Dict:
        """
        Get application statistics.

        Returns:
            Dictionary with various stats
        """
        applications = self.list_applications()

        total = len(applications)
        if total == 0:
            return {
                "total": 0,
                "active": 0,
                "by_status": {},
                "response_rate": 0,
                "avg_days_to_response": 0
            }

        # Count by status
        by_status = {}
        active = 0
        responded = 0
        days_to_response = []

        for app in applications:
            status = app.status
            by_status[status] = by_status.get(status, 0) + 1

            if app.is_active():
                active += 1

            if status != "applied":
                responded += 1

                # Calculate days to first response
                if len(app.timeline) > 1:
                    try:
                        applied = datetime.strptime(app.applied_date, "%Y-%m-%d")
                        first_response = datetime.strptime(app.timeline[1].date, "%Y-%m-%d")
                        days = (first_response - applied).days
                        days_to_response.append(days)
                    except:
                        pass

        response_rate = (responded / total * 100) if total > 0 else 0
        avg_days = sum(days_to_response) / len(days_to_response) if days_to_response else 0

        return {
            "total": total,
            "active": active,
            "by_status": by_status,
            "response_rate": round(response_rate, 1),
            "avg_days_to_response": round(avg_days, 1),
            "top_companies": self._get_top_companies(applications)
        }

    def _get_top_companies(self, applications: List[Application], limit: int = 5) -> List[Dict]:
        """Get companies with most applications"""
        company_counts = {}
        for app in applications:
            company_counts[app.company] = company_counts.get(app.company, 0) + 1

        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"company": c, "count": n} for c, n in sorted_companies[:limit]]

    # ==================== SEARCH ====================

    def search_applications(self, query: str) -> List[Application]:
        """
        Search applications by company, role, or notes.

        Args:
            query: Search query

        Returns:
            List of matching applications
        """
        applications = self.list_applications()
        query_lower = query.lower()

        results = []
        for app in applications:
            if (query_lower in app.company.lower() or
                query_lower in app.role.lower() or
                (app.notes and query_lower in app.notes.lower()) or
                (app.location and query_lower in app.location.lower())):
                results.append(app)

        return results
