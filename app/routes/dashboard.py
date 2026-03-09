"""
Dashboard Routes
Renders the main dashboard with summary statistics after login.
"""

from flask import Blueprint, render_template, session
from app.models.database import User, Employee, Department, AuditLog
from app.utils import login_required, get_current_user

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    """
    GET / or GET /dashboard
    Main landing page after login. Shows key statistics and recent activity.
    """
    current_user = get_current_user()

    # --- Statistics ---
    total_employees = Employee.query.filter_by(is_active=True).count()
    total_departments = Department.query.count()
    total_users = User.query.filter_by(is_active=True).count()

    # Count employees per department for a summary table
    departments = Department.query.all()
    dept_stats = []
    for dept in departments:
        count = Employee.query.filter_by(department_id=dept.id, is_active=True).count()
        dept_stats.append({"name": dept.name, "count": count})

    # Recent audit logs (admin only)
    recent_logs = []
    if session.get("user_role") == "admin":
        recent_logs = (
            AuditLog.query
            .order_by(AuditLog.timestamp.desc())
            .limit(10)
            .all()
        )

    # Recently added employees
    recent_employees = (
        Employee.query
        .filter_by(is_active=True)
        .order_by(Employee.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        current_user=current_user,
        total_employees=total_employees,
        total_departments=total_departments,
        total_users=total_users,
        dept_stats=dept_stats,
        recent_logs=recent_logs,
        recent_employees=recent_employees,
    )
