"""
seed_mock_bugs.py
-----------------
Pulls bugs from the running mock API server and inserts them into
your MySQL database using your existing Flask models.

Requirements:
  - mock_api_server.py must be running  (python mock/mock_api_server.py)
  - Your RRO Flask app must be configured (.env file set up)
  - At least one Engineer user must exist in the Users table

Usage (run from project root):
  python seed_mock_bugs.py
  python seed_mock_bugs.py --url http://127.0.0.1:5000   (custom server URL)
  python seed_mock_bugs.py --clear                        (wipe existing bugs first)
"""

import argparse
import re
import sys
import requests

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.bug import Bug
from app.models.bug_tests import BugTest
from app.models.bug_stations import BugStation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_bugs_from_mock(base_url):
    """
    Step 1: Login to mock server to get a token.
    Step 2: Fetch all bugs using that token.
    Returns a list of bug dicts.
    """
    print(f"[seed] Connecting to mock server at {base_url} ...")

    # Login
    try:
        r = requests.get(f"{base_url}/rest/login", params={"login": "seed", "password": "seed"}, timeout=5)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("[seed] ERROR: Cannot reach mock server.")
        print("       Make sure you ran:  python mock/mock_api_server.py")
        sys.exit(1)

    token = r.json().get("token")
    if not token:
        print("[seed] ERROR: No token returned from mock login.")
        sys.exit(1)

    print(f"[seed] Got token: {token}")

    # Fetch bugs (no version filter — get all bugs)
    r = requests.get(f"{base_url}/rest/bug", params={"token": token}, timeout=5)
    r.raise_for_status()
    bugs = r.json()

    print(f"[seed] Fetched {len(bugs)} bugs from mock server.")
    return bugs, token


def pick_engineer(session, assignee_email):
    """
    Try to find an engineer whose email matches the assignee.
    If not found, fall back to any engineer in the database.
    Returns a User object or None.
    """
    user = session.query(User).filter_by(email=assignee_email, role="Engineer").first()
    if user:
        return user
    # Fallback: any engineer
    return session.query(User).filter_by(role="Engineer").first()


def derive_bug_type(bug):
    """
    Decide if a bug is 'repro' or 'test' based on its Status or Whiteboard.
    Bugs with Status=REPRODUCE → repro
    Everything else → test
    """
    status = bug.get("Status", "").upper()
    if status == "REPRODUCE":
        return "repro"
    return "test"


def derive_priority(bug):
    """
    Map the bug's Priority field (P0–P4) to the Enum values in your DB.
    Defaults to P2 if missing or unrecognised.
    """
    raw = bug.get("Priority", "P2").upper()
    if raw in ("P0", "P1", "P2", "P3", "P4"):
        return raw
    return "P2"


def extract_test_name(comment_text):
    """
    The first comment of each mock bug contains a line like:
        Test  Name: testsrc/RemoteCopy/FCTest/...
    This function extracts just the short test filename (e.g. RCopyFCBasic).
    Returns None if not found.
    """
    match = re.search(r"Test\s+Name\s*:\s*\S+/(\w+)\.py", comment_text)
    if match:
        return match.group(1)
    return None


def extract_ring_name(comment_text):
    """
    Extracts the test ring name from the first comment, e.g. 'mockring1'.
    Used as the station name.
    Returns None if not found.
    """
    match = re.search(r"Test\s+Ring\s+Name\s*:\s*(\S+)", comment_text)
    if match:
        return match.group(1)
    return None


# ---------------------------------------------------------------------------
# Main seed logic
# ---------------------------------------------------------------------------

def seed(base_url, clear_existing):
    app = create_app()

    with app.app_context():
        bugs_data, token = fetch_bugs_from_mock(base_url)

        if clear_existing:
            print("[seed] --clear flag set. Deleting all existing bugs ...")
            BugStation.query.delete()
            BugTest.query.delete()
            Bug.query.delete()
            db.session.commit()
            print("[seed] Existing bugs cleared.")

        inserted = 0
        skipped = 0

        for raw in bugs_data:
            bug_id_str   = str(raw.get("Bug Id", ""))
            bug_code     = f"BUG-{bug_id_str}"
            assignee_email = raw.get("Assignee", "")
            summary      = raw.get("Whiteboard") or raw.get("Component", "No summary")
            priority     = derive_priority(raw)
            bug_type     = derive_bug_type(raw)
            status       = "pending"

            # Skip if this bug_code already exists in DB
            if Bug.query.filter_by(bug_code=bug_code).first():
                print(f"[seed] SKIP  {bug_code} — already in database.")
                skipped += 1
                continue

            # Find which engineer to assign
            engineer = pick_engineer(db.session, assignee_email)
            if not engineer:
                print(f"[seed] SKIP  {bug_code} — no Engineer users found in database.")
                print("       Register at least one Engineer account first, then re-run.")
                skipped += 1
                continue

            # Parse test name and ring name from first comment
            comments = raw.get("Comments", [])
            first_comment_text = comments[0]["text"] if comments else ""
            test_name  = extract_test_name(first_comment_text)
            ring_name  = extract_ring_name(first_comment_text)

            # Build the Bug row
            new_bug = Bug(
                bug_code     = bug_code,
                bug_type     = bug_type,
                priority     = priority,
                engineer_id  = engineer.id,
                summary      = summary[:255],           # DB column is VARCHAR(255)
                station_config = raw.get("Component", ""),
                resource_group = raw.get("Product", ""),
                status       = status,
            )
            db.session.add(new_bug)
            db.session.flush()   # Get new_bug.id without committing yet

            # Add test name as a BugTest row
            if test_name:
                db.session.add(BugTest(bug_id=new_bug.id, test_name=test_name))

            # Add ring name as a BugStation row
            if ring_name:
                db.session.add(BugStation(bug_id=new_bug.id, station_name=ring_name))

            db.session.commit()
            print(f"[seed] INSERT {bug_code} | {bug_type:5} | {priority} | engineer={engineer.email}")
            inserted += 1

        print(f"\n[seed] Done. Inserted={inserted}  Skipped={skipped}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed MySQL with bugs from mock API server")
    parser.add_argument("--url",   default="http://127.0.0.1:5000", help="Mock server base URL")
    parser.add_argument("--clear", action="store_true",             help="Delete all existing bugs before seeding")
    args = parser.parse_args()

    seed(args.url, args.clear)