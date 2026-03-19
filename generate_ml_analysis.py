"""
Generate ML analysis for bugs using the local mock ChatHPE API.

Usage:
    python generate_ml_analysis.py --mock-port 5001
    python generate_ml_analysis.py --mock-port 5001 --force
"""

import argparse
import json
import re
import sys
from datetime import datetime
from urllib import error, request

from sqlalchemy.exc import SQLAlchemyError

from app import create_app, db
from app.models.bug import Bug
from app.models.bug_comments import BugComment
from app.models.bug_tests import BugTest
from app.models.ml_analysis import MLAnalysis


def http_get_text(url, timeout=30):
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def http_post_json(url, payload, timeout=30):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def get_session_id(base_url):
    raw = http_get_text(f"{base_url}/v2.8/sessionId_generator").strip()
    parts = raw.split(": ", 1)
    if len(parts) != 2 or not parts[1].strip():
        raise ValueError(f"Unexpected session response: {raw}")
    return parts[1].strip()


def set_preferences(base_url, session_id):
    return http_post_json(
        f"{base_url}/v2.8/preferences",
        {"session_id": session_id, "model": "chatlite"},
    )


def call_chatlite(base_url, session_id, prompt):
    return http_post_json(
        f"{base_url}/v2.8/call/chatlite",
        {"session_id": session_id, "user_query": prompt},
    )


def build_prompt(bug, comments, test_name):
    lines = [
        f"Bug {bug.bug_code} Analysis Request",
        "",
        "You are analyzing a software bug report. Based on the following bug details and engineer comments, provide a structured analysis.",
        "",
        f"Bug ID: {bug.bug_code}",
        f"Priority: {bug.priority}",
        f"Component: {bug.summary or ''}",
        f"Test Name: {test_name}",
        "",
        "Engineer Comments:",
        "---",
    ]

    if comments:
        for idx, comment in enumerate(comments, start=1):
            creator = comment.creator or "Unknown"
            created = comment.creation_time.isoformat() if comment.creation_time else "Unknown"
            text = (comment.text or "").strip()
            lines.extend(
                [
                    f"Comment {idx} (by {creator} on {created}):",
                    text,
                    "",
                ]
            )
    else:
        lines.extend(["No engineer comments found.", ""])

    lines.extend(
        [
            "---",
            "",
            "Please provide:",
            "1. Repro Actions: Step-by-step actions needed to reproduce this bug",
            "2. Config Changes: Any configuration changes required before reproduction",
            "3. Repro Readiness: Is this bug ready to reproduce? (one of: \"Ready\", \"Needs more runs\", \"Not ready\", \"Already fixed\")",
            "4. Summary: A concise 2-3 sentence summary of the bug, root cause, and current status",
            "",
            "Format your response exactly as:",
            "REPRO_ACTIONS: <content>",
            "CONFIG_CHANGES: <content>",
            "REPRO_READINESS: <content>",
            "SUMMARY: <content>",
        ]
    )

    return "\n".join(lines)


def extract_repro_readiness(comments):
    if not comments:
        return "Needs more runs"
    text = (comments[0].text or "").strip()
    match = re.search(r"Developer\s+Progress:\s*(\S+)", text)
    if match:
        return match.group(1).strip()
    return "Needs more runs"


def strip_markdown_bold(value):
    if not value:
        return value
    return re.sub(r'\*\*.*?\*\*:?\s*', '', value).strip()


def clean_response_text(message_text):
    text = (message_text or "").strip()
    cleaned_lines = []
    for line in text.splitlines():
        if "This is a mock response" in line:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def parse_analysis_fields(message_text):
    text = clean_response_text(message_text)
    parsed = {
        "repro_actions": None,
        "config_changes": None,
        "summary": None,
    }

    patterns = {
        "repro_actions": r"\*\*Failure Signature\*\*:\s*(.*?)(?:\n\s*\n|$)",
        "config_changes": r"\*\*Key Engineer Findings\*\*:\s*(.*?)(?:\n\s*\n|$)",
        "summary": r"\*\*Reproduction Steps / Config Changes\*\*:\s*(.*?)(?:\n\s*\n|$)",
    }

    matched_any = False
    for field, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            parsed[field] = match.group(1).strip()
            matched_any = True

    if not matched_any:
        parsed["repro_actions"] = "See summary"
        parsed["config_changes"] = "See summary"
        parsed["summary"] = text
    else:
        for field in ("repro_actions", "config_changes", "summary"):
            if not parsed[field]:
                parsed[field] = "See summary"

    return parsed


def generate(mock_port, force):
    base_url = f"http://127.0.0.1:{mock_port}"

    try:
        session_id = get_session_id(base_url)
        set_preferences(base_url, session_id)
    except (error.URLError, error.HTTPError, ValueError, json.JSONDecodeError) as exc:
        print(f"Failed to initialize mock ChatHPE session: {exc}")
        sys.exit(1)

    analyzed = 0
    skipped = 0
    errors = 0
    pending_commits = 0

    app = create_app()

    with app.app_context():
        try:
            bugs = Bug.query.order_by(Bug.id.asc()).all()

            for bug in bugs:
                existing = MLAnalysis.query.filter_by(bug_id=bug.id).first()

                has_summary = existing and existing.summary is not None
                has_bug_unknown = has_summary and "Bug UNKNOWN" in (existing.summary or "")

                if not force and has_summary and not has_bug_unknown:
                    print(f"[{bug.bug_code}] Skipping - already analyzed (use --force to regenerate)")
                    skipped += 1
                    continue

                comments = (
                    BugComment.query
                    .filter_by(bug_id=bug.id)
                    .order_by(BugComment.comment_bugzilla_id.asc(), BugComment.id.asc())
                    .all()
                )

                first_test = BugTest.query.filter_by(bug_id=bug.id).first()
                test_name = (first_test.test_name or "N/A") if first_test else "N/A"

                prompt = build_prompt(bug, comments, test_name)

                try:
                    response = call_chatlite(base_url, session_id, prompt)
                    message = response.get("message", "")
                    parsed = parse_analysis_fields(message)
                except (error.URLError, error.HTTPError, ValueError, json.JSONDecodeError) as exc:
                    print(f"[{bug.bug_code}] Error - failed to generate analysis: {exc}")
                    errors += 1
                    continue

                if existing is None:
                    existing = MLAnalysis(bug_id=bug.id)
                    db.session.add(existing)

                existing.repro_actions = strip_markdown_bold(parsed["repro_actions"])
                existing.config_changes = strip_markdown_bold(parsed["config_changes"])
                existing.repro_readiness = strip_markdown_bold(extract_repro_readiness(comments))
                existing.summary = strip_markdown_bold(parsed["summary"])
                existing.generated_at = datetime.utcnow()

                analyzed += 1
                pending_commits += 1
                print(f"[{bug.bug_code}] Generating analysis... Done")

                if pending_commits >= 5:
                    db.session.commit()
                    pending_commits = 0

            if pending_commits > 0:
                db.session.commit()

            print("ML Analysis generation complete.")
            print(f"  Analyzed: {analyzed}")
            print(f"  Skipped:  {skipped}")
            print(f"  Errors:   {errors}")

        except SQLAlchemyError as exc:
            db.session.rollback()
            print(f"Database error while generating ML analysis: {exc}")
            sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate ML analysis using local mock ChatHPE API")
    parser.add_argument(
        "--mock-port",
        type=int,
        default=5001,
        help="Port where mock_api_server.py is running (default: 5001)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate analysis even if summary already exists",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate(args.mock_port, args.force)
