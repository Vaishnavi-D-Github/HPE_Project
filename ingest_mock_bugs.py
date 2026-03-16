"""
ingest_mock_bugs.py
-------------------
One-time script: reads mock_bugs.json, populates the DB, and calls the mock
ChatHPE server to generate ML analysis for each bug.

Run order:
  Terminal 1:  python mock_api_server.py --port 8080
  Terminal 2:  python ingest_mock_bugs.py
               python run.py
"""

import json
import os
import re
import sys
from datetime import datetime

import requests  # pip install requests

from app import create_app, db
from app.models.bug import Bug
from app.models.bug_comments import BugComment
from app.models.bug_tests import BugTest
from app.models.ml_analysis import MLAnalysis
from app.models.user import User


MOCK_BUGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_bugs.json")

# Address where mock_api_server.py is running.
# Use port 8080 so it doesn't clash with run.py on 5000.
CHATHPE_URL = "http://127.0.0.1:8080"


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_spaces(value):
    """Collapses multiple spaces/tabs into one space."""
    return re.sub(r"\s+", " ", value).strip()


def parse_execution_datetime(raw_value):
    """'2024-05-01 08:30:00.000000 UTC' → datetime object"""
    if not raw_value:
        return None
    clean = raw_value.strip()
    if clean.endswith(" UTC"):
        clean = clean[:-4]
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


def parse_iso_datetime(raw_value):
    """'2024-05-01T08:30:00Z' → datetime object"""
    if not raw_value:
        return None
    clean = raw_value.strip()
    if clean.endswith("Z"):
        clean = clean[:-1]
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


def parse_int(raw_value):
    if raw_value is None:
        return None
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError):
        return None


def parse_test_metadata(comment_text):
    """
    Parses the tab-separated metadata block from comment[0].text.
    Each line is  'Key: Value'  — keys are space-normalised.
    """
    parsed = {}
    if not comment_text:
        return parsed
    for line in comment_text.splitlines():
        clean_line = line.strip()
        if not clean_line or ":" not in clean_line:
            continue
        key, value = clean_line.split(":", 1)
        key   = normalize_spaces(key)
        value = value.strip()
        parsed[key] = value
    return parsed


def get_metadata_comment(comments):
    if not comments:
        return {}
    first = comments[0]
    return first if isinstance(first, dict) else {}


def map_bug_status(source_status):
    status = (source_status or "").strip().upper()
    if status == "REPRODUCE":
        return "running"
    if status == "OPEN":
        return "pending"
    if status in ("CLOSED", "VERIFIED"):
        return "completed"
    return "pending"


def map_bug_type(source_status):
    status = (source_status or "").strip().upper()
    return "repro" if status == "REPRODUCE" else "test"


# ── ML Analysis helpers ───────────────────────────────────────────────────────

def extract_section(text, keyword):
    """Pulls out the paragraph after a keyword heading in the markdown response."""
    lines      = text.splitlines()
    collecting = False
    result     = []
    for line in lines:
        if keyword.lower() in line.lower():
            collecting = True
            continue
        if collecting:
            if line.strip().startswith("**") and result:
                break
            if line.strip():
                result.append(line.strip())
    return " ".join(result).strip() or text[:300]


def generate_ml_analysis(bug_code, comments):
    """
    Sends the bug's comment thread to the mock ChatHPE server
    and returns a dict with repro_actions, config_changes,
    repro_readiness, and summary.
    Returns None if the server is not reachable.
    """
    comment_texts = [
        c["text"] for c in comments
        if isinstance(c, dict) and c.get("text")
    ]
    if not comment_texts:
        return None

    prompt = (
        f"Bug {bug_code} - Engineer Comments:\n\n"
        + "\n\n---\n\n".join(comment_texts)
        + "\n\nFrom the above engineer thread, extract:\n"
          "1. **Repro Actions**: Step-by-step instructions to reproduce the bug\n"
          "2. **Config Changes**: Any configuration changes needed before reproducing\n"
          "3. **Repro Readiness**: Is this ready to reproduce? (Yes / No / Partial)\n"
          "4. **Summary**: One paragraph summary of the issue and current state\n"
    )

    try:
        resp = requests.post(
            f"{CHATHPE_URL}/v2.8/call/chatlite",
            json={"user_query": prompt},
            timeout=10,
        )
        resp.raise_for_status()
        message = resp.json().get("message", "")
        return {
            "repro_actions":   extract_section(message, "Repro Actions"),
            "config_changes":  extract_section(message, "Config Changes"),
            "repro_readiness": extract_section(message, "Repro Readiness"),
            "summary":         message,
        }
    except requests.exceptions.ConnectionError:
        print(f"  [ML] Cannot connect to mock server at {CHATHPE_URL}.")
        print(f"       Start it first:  python mock_api_server.py --port 8080")
        return None
    except Exception as e:
        print(f"  [ML] ChatHPE call failed for bug {bug_code}: {e}")
        return None


# ── Main ingest ───────────────────────────────────────────────────────────────

def ingest():
    try:
        with open(MOCK_BUGS_FILE, "r", encoding="utf-8") as f:
            bug_rows = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: mock_bugs.json not found at {MOCK_BUGS_FILE}")
        sys.exit(1)

    inserted_bugs    = 0
    skipped_bugs     = 0
    created_tests    = 0
    created_comments = 0
    created_ml       = 0
    ml_failed        = 0

    app = create_app()

    with app.app_context():
        try:
            for row in bug_rows:
                bug_code = str(row.get("Bug Id", "")).strip()
                if not bug_code:
                    continue

                # Skip if already ingested — safe to re-run
                if Bug.query.filter_by(bug_code=bug_code).first():
                    print(f"  Skipping bug {bug_code} — already exists")
                    skipped_bugs += 1
                    continue

                source_status  = row.get("Status")
                assignee_email = (row.get("Assignee") or "").strip()

                engineer = None
                if assignee_email:
                    engineer = User.query.filter(
                        db.func.lower(User.email) == assignee_email.lower()
                    ).first()

                # Insert Bug row
                bug_obj = Bug(
                    bug_code=bug_code,
                    priority=(row.get("Priority") or "P2").strip(),
                    status=map_bug_status(source_status),
                    engineer_id=engineer.id if engineer else None,
                    bug_type=map_bug_type(source_status),
                    resource_group=(row.get("Build") or "").strip() or None,
                    summary=(row.get("Component") or "").strip() or None,
                )
                db.session.add(bug_obj)
                db.session.flush()  # get bug_obj.id without committing

                # Parse test metadata from comment[0]
                comments         = row.get("Comments") or []
                metadata_comment = get_metadata_comment(comments)
                metadata         = parse_test_metadata(metadata_comment.get("text", ""))

                raw_test_name = metadata.get("Test Name")
                test_name     = None
                if raw_test_name:
                    test_name = raw_test_name.replace("\\", "/").rsplit("/", 1)[-1]

                test_ring_name = metadata.get("Test Ring Name")

                # Insert Bug_Tests row
                bug_test = BugTest(
                    bug_id=bug_obj.id,
                    test_name=test_name,
                    test_plan_name=metadata.get("Test Plan Name"),
                    test_ring_name=test_ring_name,
                    execution_start=parse_execution_datetime(metadata.get("Execution Start")),
                    execution_end=parse_execution_datetime(metadata.get("Execution End")),
                    controller_types=metadata.get("Controller Types"),
                    number_of_nodes=parse_int(metadata.get("Number Of Nodes")),
                    failure_type=metadata.get("Failure Type"),
                    build_version=metadata.get("Build Version"),
                    nfs_path=metadata.get("NFS Path"),
                    odin_link=metadata.get("Odin Link"),
                    signature=metadata.get("Signature"),
                    station_name=test_ring_name,
                )
                db.session.add(bug_test)
                created_tests += 1

                # Insert Bug_Comments rows
                for comment in comments:
                    if not isinstance(comment, dict):
                        continue
                    db.session.add(BugComment(
                        bug_id=bug_obj.id,
                        comment_bugzilla_id=parse_int(comment.get("id")),
                        creator=comment.get("creator"),
                        creation_time=parse_iso_datetime(comment.get("creation_time")),
                        text=comment.get("text"),
                    ))
                    created_comments += 1

                # Call ChatHPE and insert ML_Analysis row
                print(f"  [ML] Generating analysis for bug {bug_code}...")
                ml_data = generate_ml_analysis(bug_code, comments)

                db.session.add(MLAnalysis(
                    bug_id=bug_obj.id,
                    repro_actions=ml_data["repro_actions"]   if ml_data else None,
                    config_changes=ml_data["config_changes"]  if ml_data else None,
                    repro_readiness=ml_data["repro_readiness"] if ml_data else None,
                    summary=ml_data["summary"]          if ml_data else None,
                ))

                if ml_data:
                    created_ml += 1
                else:
                    ml_failed += 1

                inserted_bugs += 1
                print(f"  Inserted bug {bug_code}")

            db.session.commit()

        except Exception as exc:
            db.session.rollback()
            print(f"\nIngest FAILED: {exc}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print("\n── Ingest complete ──────────────────────────────")
    print(f"  Bugs inserted      : {inserted_bugs}")
    print(f"  Bugs skipped       : {skipped_bugs}")
    print(f"  Tests created      : {created_tests}")
    print(f"  Comments created   : {created_comments}")
    print(f"  ML analyses saved  : {created_ml}")
    print(f"  ML analyses failed : {ml_failed}")
    if ml_failed:
        print("\n  NOTE: ML failures mean mock_api_server.py was not running.")
        print("  Re-run with the server active to populate ML analysis.")


if __name__ == "__main__":
    ingest()