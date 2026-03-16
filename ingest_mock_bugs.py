"""
Ingest bugs from mock_bugs.json into the database.

Usage:
    python ingest_mock_bugs.py
"""

import json
import os
import re
import sys
from datetime import datetime

from app import create_app, db
from app.models.bug import Bug
from app.models.bug_comments import BugComment
from app.models.bug_tests import BugTest
from app.models.ml_analysis import MLAnalysis
from app.models.user import User


MOCK_BUGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_bugs.json")


def normalize_spaces(value):
    return re.sub(r"\s+", " ", value).strip()


def parse_execution_datetime(raw_value):
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
    parsed = {}

    if not comment_text:
        return parsed

    for line in comment_text.splitlines():
        clean_line = line.strip()
        if not clean_line or ":" not in clean_line:
            continue

        key, value = clean_line.split(":", 1)
        key = normalize_spaces(key)
        value = value.strip()
        parsed[key] = value

    return parsed


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


def get_metadata_comment(comments):
    if not comments:
        return {}

    first = comments[0]
    if isinstance(first, dict):
        return first

    return {}


def ingest():
    with open(MOCK_BUGS_FILE, "r", encoding="utf-8") as handle:
        bug_rows = json.load(handle)

    inserted_bugs = 0
    skipped_bugs = 0
    created_tests = 0
    created_comments = 0
    created_ml = 0

    app = create_app()

    with app.app_context():
        try:
            for row in bug_rows:
                bug_code = str(row.get("Bug Id", "")).strip()
                if not bug_code:
                    continue

                existing = Bug.query.filter_by(bug_code=bug_code).first()
                if existing:
                    print(f"Skipping bug {bug_code} -- already exists")
                    skipped_bugs += 1
                    continue

                source_status = row.get("Status")
                assignee_email = (row.get("Assignee") or "").strip()

                engineer = None
                if assignee_email:
                    engineer = User.query.filter(db.func.lower(User.email) == assignee_email.lower()).first()

                bug = Bug(
                    bug_code=bug_code,
                    priority=(row.get("Priority") or "P2").strip(),
                    status=map_bug_status(source_status),
                    engineer_id=engineer.id if engineer else None,
                    bug_type=map_bug_type(source_status),
                    resource_group=(row.get("Build") or "").strip() or None,
                    summary=(row.get("Component") or "").strip() or None,
                )
                db.session.add(bug)
                db.session.flush()

                comments = row.get("Comments") or []
                metadata_comment = get_metadata_comment(comments)
                metadata = parse_test_metadata(metadata_comment.get("text", ""))

                raw_test_name = metadata.get("Test Name")
                test_name = None
                if raw_test_name:
                    test_name = raw_test_name.replace("\\", "/").rsplit("/", 1)[-1]

                test_ring_name = metadata.get("Test Ring Name")

                bug_test = BugTest(
                    bug_id=bug.id,
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

                for comment in comments:
                    comment_obj = BugComment(
                        bug_id=bug.id,
                        comment_bugzilla_id=parse_int(comment.get("id")) if isinstance(comment, dict) else None,
                        creator=(comment.get("creator") if isinstance(comment, dict) else None),
                        creation_time=parse_iso_datetime(comment.get("creation_time")) if isinstance(comment, dict) else None,
                        text=(comment.get("text") if isinstance(comment, dict) else None),
                    )
                    db.session.add(comment_obj)
                    created_comments += 1

                ml_analysis = MLAnalysis(
                    bug_id=bug.id,
                    repro_actions=None,
                    config_changes=None,
                    repro_readiness=None,
                    summary=None,
                )
                db.session.add(ml_analysis)
                created_ml += 1

                inserted_bugs += 1

            db.session.commit()

            print("Ingest complete.")
            print(f"  Bugs inserted: {inserted_bugs}")
            print(f"  Bugs skipped:  {skipped_bugs}")
            print(f"  Tests created: {created_tests}")
            print(f"  Comments created: {created_comments}")
            print(f"  ML Analysis placeholders created: {created_ml}")
        except Exception as exc:
            db.session.rollback()
            print(f"Ingest failed: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    ingest()
