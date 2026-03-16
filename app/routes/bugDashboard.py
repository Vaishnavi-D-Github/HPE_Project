from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from app.extensions import db
from app.models.bug import Bug
from app.models.bug_tests import BugTest
from app.models.bug_stations import BugStation
from app.models.user import User
from app.models.workgroup import Workgroup
from app.models.workgroupAssignment import WorkgroupAssignment
from app.auth_utils import get_current_auth_token, get_current_role, get_current_user, get_current_user_id
from sqlalchemy import select, or_

bug = Blueprint("bugDashboard", __name__)


# --------------------------------------------------
# BUG MANAGEMENT PAGE
# --------------------------------------------------
@bug.route("/bug_management")
def bug_management():
    current_user_id = get_current_user_id()
    current_role = get_current_role()

    if not current_user_id:
        return redirect(url_for("auth.login"))

    workgroup_id = request.args.get('workgroup_id', type=int)
    workgroup = None

    if workgroup_id:
        workgroup = Workgroup.query.get(workgroup_id)
        if not workgroup:
            return redirect(url_for("manager.manager_dashboard"))

        if current_role == 'Manager' and workgroup.manager_id != current_user_id:
            return redirect(url_for("manager.manager_dashboard"))

    return render_template("bugManagement.html", workgroup=workgroup, auth_token=get_current_auth_token())


# --------------------------------------------------
# GET ALL BUGS
# --------------------------------------------------
@bug.route("/api/bugs", methods=["GET"])
def get_bugs():

    user_id = get_current_user_id()
    role = get_current_role()

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    workgroup_id = request.args.get('workgroup_id', type=int)
    my_only = request.args.get('my_only', 'false').lower() == 'true'

    if workgroup_id:
        workgroup = Workgroup.query.get(workgroup_id)
        if not workgroup:
            return jsonify({"error": "Workgroup not found"}), 404
        if role == 'Manager' and workgroup.manager_id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

    query = Bug.query

    if workgroup_id:
        engineer_ids = db.session.query(WorkgroupAssignment.employee_id).filter(
            WorkgroupAssignment.workgroup_id == workgroup_id
        ).all()
        engineer_ids = [e[0] for e in engineer_ids]

        if not engineer_ids:
            return jsonify({"repro": [], "test": []})

        query = query.filter(Bug.engineer_id.in_(engineer_ids))

        if role == "Engineer" and my_only:
            query = query.filter(Bug.engineer_id == user_id)

    elif role == "Manager":
        engineer_ids_subq = (
            db.session.query(db.func.distinct(WorkgroupAssignment.employee_id))
            .join(Workgroup, WorkgroupAssignment.workgroup_id == Workgroup.id)
            .filter(Workgroup.manager_id == user_id)
            .subquery()
        )
        engineer_ids = select(WorkgroupAssignment.employee_id).join(
            Workgroup,
            Workgroup.id == WorkgroupAssignment.workgroup_id
        ).where(
            Workgroup.manager_id == user_id
        )
        query = query.filter(Bug.engineer_id.in_(engineer_ids))

    elif role == "Engineer":
        query = query.filter(Bug.engineer_id == user_id)

    bugs = query.all()
    repro = []
    test = []

    for b in bugs:
        data = {
            "id": b.bug_code,
            "priority": b.priority,
            "engineer": {
                "name": b.engineer.full_name if b.engineer else "Unassigned",
                "initials": (
                    (b.engineer.first_name[0] + b.engineer.last_name[0]).upper()
                    if b.engineer else "--"
                ),
                "color": "#7c3aed"
            },
            "summary": b.summary or "",
            "tests": [t.test_name for t in b.tests],
            "test_count": len(b.tests),
            "stations": [s.station_name for s in b.stations],
            "config": b.station_config,
            "resourceGroup": b.resource_group
        }
        if b.bug_type == "repro":
            repro.append(data)
        else:
            test.append(data)

    return jsonify({"repro": repro, "test": test})


# --------------------------------------------------
# UPDATE RESOURCE GROUP
# --------------------------------------------------
@bug.route("/api/bugs/<bug_code>/resource", methods=["PATCH"])
def update_resource_group(bug_code):
    data = request.json
    bug = Bug.query.filter_by(bug_code=bug_code).first()
    bug.resource_group = data.get("resourceGroup")
    db.session.commit()
    return jsonify({"message": "Resource group updated"})


# --------------------------------------------------
# RUN BUG NOW
# --------------------------------------------------
@bug.route("/api/bugs/<bug_code>/run", methods=["POST"])
def run_bug_now(bug_code):
    bug = Bug.query.filter_by(bug_code=bug_code).first()
    bug.status = "running"
    db.session.commit()
    return jsonify({"message": "Bug execution started"})


# --------------------------------------------------
# RUN BUG LATER
# --------------------------------------------------
@bug.route("/api/bugs/<bug_code>/schedule", methods=["POST"])
def schedule_bug(bug_code):
    bug = Bug.query.filter_by(bug_code=bug_code).first()
    bug.status = "scheduled"
    db.session.commit()
    return jsonify({"message": "Bug scheduled"})


# --------------------------------------------------
# BUG STATISTICS
# --------------------------------------------------
@bug.route("/api/bugs/stats", methods=["GET"])
def bug_stats():

    user_id = get_current_user_id()
    role = get_current_role()

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    workgroup_id = request.args.get('workgroup_id', type=int)
    my_only = request.args.get('my_only', 'false').lower() == 'true'

    if workgroup_id:
        workgroup = Workgroup.query.get(workgroup_id)
        if not workgroup:
            return jsonify({"error": "Workgroup not found"}), 404
        if role == 'Manager' and workgroup.manager_id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

    query = Bug.query

    if workgroup_id:
        engineer_ids = db.session.query(WorkgroupAssignment.employee_id).filter(
            WorkgroupAssignment.workgroup_id == workgroup_id
        ).all()
        engineer_ids = [e[0] for e in engineer_ids]

        if not engineer_ids:
            return jsonify({"totalBugs": 0, "reproBugs": 0, "testBugs": 0, "pendingActions": 0})

        query = query.filter(Bug.engineer_id.in_(engineer_ids))

        if role == "Engineer" and my_only:
            query = query.filter(Bug.engineer_id == user_id)

    elif role == "Manager":
        engineer_ids_subq = (
            db.session.query(db.func.distinct(WorkgroupAssignment.employee_id))
            .join(Workgroup, WorkgroupAssignment.workgroup_id == Workgroup.id)
            .filter(Workgroup.manager_id == user_id)
            .subquery()
        )
        query = query.filter(Bug.engineer_id.in_(engineer_ids_subq))

    elif role == "Engineer":
        query = query.filter(Bug.engineer_id == user_id)

    total   = query.count()
    repro   = query.filter_by(bug_type="repro").count()
    test    = query.filter_by(bug_type="test").count()
    pending = query.filter_by(status="pending").count()

    return jsonify({
        "totalBugs": total,
        "reproBugs": repro,
        "testBugs": test,
        "pendingActions": pending
    })


# --------------------------------------------------
# SEARCH BUGS (autocomplete suggestions)
# --------------------------------------------------
@bug.route("/api/bugs/search", methods=["GET"])
def search_bugs():

    user_id = get_current_user_id()
    role = get_current_role()

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    workgroup_id    = request.args.get("workgroup_id", type=int)
    my_only         = request.args.get('my_only', 'false').lower() == 'true'
    pattern         = f"%{q}%"
    MAX_SUGGESTIONS = 7

    base_query = Bug.query

    if workgroup_id:
        engineer_ids = db.session.query(WorkgroupAssignment.employee_id).filter(
            WorkgroupAssignment.workgroup_id == workgroup_id
        ).all()
        engineer_ids = [e[0] for e in engineer_ids]
        if not engineer_ids:
            return jsonify([])
        base_query = base_query.filter(Bug.engineer_id.in_(engineer_ids))

        if role == "Engineer" and my_only:
            base_query = base_query.filter(Bug.engineer_id == user_id)
    elif role == "Manager":
        engineer_ids = select(WorkgroupAssignment.employee_id).join(
            Workgroup, Workgroup.id == WorkgroupAssignment.workgroup_id
        ).where(Workgroup.manager_id == user_id)
        base_query = base_query.filter(Bug.engineer_id.in_(engineer_ids))
    elif role == "Engineer":
        base_query = base_query.filter(Bug.engineer_id == user_id)

    suggestions = []
    seen = set()

    def add_suggestion(type_label, value, bug_code):
        key = (type_label, value)
        if key not in seen and len(suggestions) < MAX_SUGGESTIONS:
            seen.add(key)
            suggestions.append({"type": type_label, "value": value, "bug_code": bug_code})

    for b in base_query.filter(Bug.bug_code.ilike(pattern)).limit(MAX_SUGGESTIONS).all():
        add_suggestion("Bug ID", b.bug_code, b.bug_code)

    if len(suggestions) < MAX_SUGGESTIONS:
        for b in base_query.join(User, Bug.engineer_id == User.id).filter(
            or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                db.func.concat(User.first_name, ' ', User.last_name).ilike(pattern)
            )
        ).limit(MAX_SUGGESTIONS).all():
            if b.engineer:
                add_suggestion("Engineer", b.engineer.full_name, b.bug_code)

    if len(suggestions) < MAX_SUGGESTIONS:
        for b in base_query.join(BugTest, Bug.id == BugTest.bug_id).filter(
            BugTest.test_name.ilike(pattern)
        ).limit(MAX_SUGGESTIONS).all():
            for t in b.tests:
                if t.test_name and q.lower() in t.test_name.lower():
                    add_suggestion("Test", t.test_name, b.bug_code)

    if len(suggestions) < MAX_SUGGESTIONS:
        for b in base_query.join(BugStation, Bug.id == BugStation.bug_id).filter(
            BugStation.station_name.ilike(pattern)
        ).limit(MAX_SUGGESTIONS).all():
            for s in b.stations:
                if s.station_name and q.lower() in s.station_name.lower():
                    add_suggestion("Station", s.station_name, b.bug_code)

    return jsonify(suggestions)


# --------------------------------------------------
# GET TESTS FOR A BUG (expandable row)
# --------------------------------------------------
@bug.route("/api/bugs/<bug_code>/tests", methods=["GET"])
def get_bug_tests(bug_code):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    b = Bug.query.filter_by(bug_code=bug_code).first()
    if not b:
        return jsonify({"error": "Bug not found"}), 404

    tests = []
    for t in b.tests:
        tests.append({
            "test_name":        t.test_name or "",
            "station_name":     t.station_name or "",
            "test_ring_name":   t.test_ring_name or "",
            "controller_types": t.controller_types or "",
            "number_of_nodes":  t.number_of_nodes,
            "build_version":    t.build_version or "",
            "nfs_path":         t.nfs_path or "",
            "odin_link":        t.odin_link or "",
            "signature":        t.signature or "",
        })

    return jsonify({"bug_code": bug_code, "tests": tests})


# --------------------------------------------------
# GET ML ANALYSIS FOR A BUG (expandable row)
# --------------------------------------------------
@bug.route("/api/bugs/<bug_code>/analysis", methods=["GET"])
def get_bug_analysis(bug_code):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    b = Bug.query.filter_by(bug_code=bug_code).first()
    if not b:
        return jsonify({"error": "Bug not found"}), 404

    ml = b.ml_analysis
    if not ml:
        return jsonify({"bug_code": bug_code, "analysis": None})

    return jsonify({
        "bug_code": bug_code,
        "analysis": {
            "repro_actions":   ml.repro_actions or "",
            "config_changes":  ml.config_changes or "",
            "repro_readiness": ml.repro_readiness or "",
            "summary":         ml.summary or "",
        }
    })