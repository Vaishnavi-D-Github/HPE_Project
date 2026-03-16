# app/services/bug_sync.py

import requests
import json
from app.staging_db import get_staging_session
from app.models.staged_bug import StagedBug
from app.config import Config


def fetch_and_sync_bugs():
    """
    Called on every login.
    1. Logs into external bug API → gets token.
    2. Fetches all bugs.
    3. CLEARS the staging DB table.
    4. Inserts all freshly fetched bugs into rro_staging.staged_bugs.
    """

    # Step 1: Login to external API
    try:
        login_resp = requests.get(
            f"{Config.BUG_API_BASE_URL}/rest/login",
            params={
                "login": Config.BUG_API_USER,
                "password": Config.BUG_API_PASSWORD
            },
            timeout=10
        )
        login_resp.raise_for_status()
        token = login_resp.json().get("token")
        if not token:
            print("[BugSync] No token returned from API login.")
            return
    except Exception as e:
        print(f"[BugSync] Login failed: {e}")
        return

    # Step 2: Fetch bugs
    try:
        bugs_resp = requests.get(
            f"{Config.BUG_API_BASE_URL}/rest/bug",
            params={"token": token, "version": Config.BUG_API_VERSION},
            timeout=15
        )
        bugs_resp.raise_for_status()
        bugs_data = bugs_resp.json()
    except Exception as e:
        print(f"[BugSync] Bug fetch failed: {e}")
        return

    # Step 3 & 4: Clear staging table and refill it
    session = get_staging_session()
    try:
        session.query(StagedBug).delete()   # wipe old data
        session.commit()

        for bug in bugs_data:
            bug_code = str(bug.get("Bug Id", "")).strip()
            if not bug_code:
                continue

            staged = StagedBug(
                bug_code      = bug_code,
                product       = bug.get("Product", ""),
                component     = bug.get("Component", ""),
                status        = bug.get("Status", ""),
                assignee      = bug.get("Assignee", ""),
                reporter      = bug.get("Reporter", ""),
                priority      = bug.get("Priority", "P2"),
                severity      = bug.get("Severity", ""),
                build_version = bug.get("Build", ""),
                summary       = bug.get("Component", ""),
                comments_json = json.dumps(bug.get("Comments", []))
            )
            session.add(staged)

        session.commit()
        print(f"[BugSync] Staging DB refreshed with {len(bugs_data)} bugs.")
    except Exception as e:
        session.rollback()
        print(f"[BugSync] Staging DB write failed: {e}")
    finally:
        session.close()