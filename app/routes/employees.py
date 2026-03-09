"""
Employee Management Routes
Full CRUD for employee records with role-based access control.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.models.database import db, Employee, Department
from app.utils import login_required, admin_required, get_current_user, log_action

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


# -----------------------------------------------------------------------------
# LIST + SEARCH
# -----------------------------------------------------------------------------
@employees_bp.route("/")
@login_required
def list_employees():
    """
    GET /employees/
    Display all active employees. Supports search by name, email, or department.
    """
    search_query = request.args.get("q", "").strip()
    dept_filter = request.args.get("department", "").strip()

    query = Employee.query.filter_by(is_active=True)

    if search_query:
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(f"%{search_query}%"),
                Employee.last_name.ilike(f"%{search_query}%"),
                Employee.email.ilike(f"%{search_query}%"),
                Employee.job_title.ilike(f"%{search_query}%"),
            )
        )

    if dept_filter:
        query = query.join(Department).filter(Department.name == dept_filter)

    employees = query.order_by(Employee.last_name).all()
    departments = Department.query.order_by(Department.name).all()
    current_user = get_current_user()

    return render_template(
        "employees/list.html",
        employees=employees,
        departments=departments,
        search_query=search_query,
        dept_filter=dept_filter,
        current_user=current_user,
    )


# -----------------------------------------------------------------------------
# VIEW SINGLE EMPLOYEE
# -----------------------------------------------------------------------------
@employees_bp.route("/<int:employee_id>")
@login_required
def view_employee(employee_id):
    """
    GET /employees/<id>
    View detailed profile of a single employee.
    """
    employee = Employee.query.get_or_404(employee_id)
    current_user = get_current_user()
    return render_template("employees/view.html", employee=employee, current_user=current_user)


# -----------------------------------------------------------------------------
# ADD EMPLOYEE
# -----------------------------------------------------------------------------
@employees_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_employee():
    """
    GET  /employees/add  – Render add employee form.
    POST /employees/add  – Create a new employee record.
    """
    departments = Department.query.order_by(Department.name).all()
    current_user = get_current_user()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        job_title = request.form.get("job_title", "").strip()
        salary = request.form.get("salary", "").strip()
        hire_date_str = request.form.get("hire_date", "").strip()
        department_id = request.form.get("department_id", "").strip()

        # Validation
        errors = []
        if not first_name:
            errors.append("First name is required.")
        if not last_name:
            errors.append("Last name is required.")
        if not email:
            errors.append("Email is required.")
        elif Employee.query.filter_by(email=email).first():
            errors.append("An employee with this email already exists.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("employees/form.html", departments=departments,
                                   form_data=request.form, current_user=current_user,
                                   action="add")

        # Parse optional fields
        hire_date = None
        if hire_date_str:
            try:
                hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid hire date format.", "warning")

        salary_val = None
        if salary:
            try:
                salary_val = float(salary)
            except ValueError:
                flash("Invalid salary value.", "warning")

        employee = Employee(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone or None,
            job_title=job_title or None,
            salary=salary_val,
            hire_date=hire_date,
            department_id=int(department_id) if department_id else None,
        )
        db.session.add(employee)
        db.session.commit()

        log_action("CREATE_EMPLOYEE", resource="employee", resource_id=employee.id)
        flash(f"Employee {employee.full_name} added successfully.", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("employees/form.html", departments=departments,
                           form_data={}, current_user=current_user, action="add")


# -----------------------------------------------------------------------------
# EDIT EMPLOYEE
# -----------------------------------------------------------------------------
@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    """
    GET  /employees/<id>/edit  – Render pre-populated edit form.
    POST /employees/<id>/edit  – Update an existing employee record.
    """
    employee = Employee.query.get_or_404(employee_id)
    departments = Department.query.order_by(Department.name).all()
    current_user = get_current_user()

    if request.method == "POST":
        employee.first_name = request.form.get("first_name", employee.first_name).strip()
        employee.last_name = request.form.get("last_name", employee.last_name).strip()
        employee.email = request.form.get("email", employee.email).strip()
        employee.phone = request.form.get("phone", "").strip() or None
        employee.job_title = request.form.get("job_title", "").strip() or None

        salary_str = request.form.get("salary", "").strip()
        if salary_str:
            try:
                employee.salary = float(salary_str)
            except ValueError:
                flash("Invalid salary value – keeping existing.", "warning")

        hire_date_str = request.form.get("hire_date", "").strip()
        if hire_date_str:
            try:
                employee.hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid hire date – keeping existing.", "warning")

        dept_id = request.form.get("department_id", "").strip()
        employee.department_id = int(dept_id) if dept_id else None
        employee.updated_at = datetime.utcnow()

        db.session.commit()

        log_action("UPDATE_EMPLOYEE", resource="employee", resource_id=employee.id)
        flash(f"Employee {employee.full_name} updated successfully.", "success")
        return redirect(url_for("employees.view_employee", employee_id=employee.id))

    return render_template("employees/form.html", departments=departments,
                           employee=employee, form_data={}, current_user=current_user,
                           action="edit")


# -----------------------------------------------------------------------------
# DELETE EMPLOYEE (Admin Only)
# -----------------------------------------------------------------------------
@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@admin_required
def delete_employee(employee_id):
    """
    POST /employees/<id>/delete
    Soft-delete an employee record. Admin only.
    """
    employee = Employee.query.get_or_404(employee_id)
    employee.is_active = False
    db.session.commit()

    log_action("DELETE_EMPLOYEE", resource="employee", resource_id=employee_id)
    flash(f"Employee {employee.full_name} has been removed.", "warning")
    return redirect(url_for("employees.list_employees"))
