"""
Database Models
Defines SQLAlchemy ORM models for the Employee Management Portal.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# =============================================================================
# USER MODEL
# =============================================================================
class User(db.Model):
    """
    Represents an application user (Admin or regular User).
    Handles authentication credentials and role assignments.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'admin' or 'user'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationship: a user can upload many files
    uploaded_files = db.relationship("EmployeeFile", backref="uploader", lazy=True)

    def set_password(self, password):
        """Hash and store the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has admin role."""
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"


# =============================================================================
# DEPARTMENT MODEL
# =============================================================================
class Department(db.Model):
    """
    Represents a company department. Employees belong to a department.
    """
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: department has many employees
    employees = db.relationship("Employee", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# =============================================================================
# EMPLOYEE MODEL
# =============================================================================
class Employee(db.Model):
    """
    Represents an employee record in the system.
    Core entity for the Employee Management Portal.
    """
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    salary = db.Column(db.Float, nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Key to Department
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    # Relationship: employee can have many files
    files = db.relationship("EmployeeFile", backref="employee", lazy=True, cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Employee {self.full_name}>"


# =============================================================================
# EMPLOYEE FILE MODEL
# =============================================================================
class EmployeeFile(db.Model):
    """
    Represents a file/document uploaded for an employee.
    Tracks upload metadata and file storage location.
    """
    __tablename__ = "employee_files"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    original_filename = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(50), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # in bytes
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<EmployeeFile {self.original_filename}>"


# =============================================================================
# AUDIT LOG MODEL
# =============================================================================
class AuditLog(db.Model):
    """
    Tracks significant user actions for auditing and security review.
    NOTE: In Phase 2, this will be used to demonstrate logging gaps.
    """
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="success")  # success / failure
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog {self.action} by user_id={self.user_id}>"


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================
def init_db(app):
    """
    Create all tables and seed initial data if the database is empty.
    """
    db.create_all()
    _seed_initial_data()


def _seed_initial_data():
    """
    Seed the database with default admin user, sample departments,
    and sample employees for demonstration purposes.
    """
    # Only seed if no users exist
    if User.query.first():
        return

    # --- Seed Admin User ---
    admin = User(
        username="admin",
        email="admin@enterprise.local",
        role="admin",
        is_active=True,
    )
    admin.set_password("Admin@1234")

    # --- Seed Regular User ---
    user = User(
        username="jdoe",
        email="jdoe@enterprise.local",
        role="user",
        is_active=True,
    )
    user.set_password("User@1234")

    db.session.add_all([admin, user])

    # --- Seed Departments ---
    departments = [
        Department(name="Engineering", description="Software and infrastructure engineering"),
        Department(name="Human Resources", description="Talent acquisition and people operations"),
        Department(name="Finance", description="Financial planning and accounting"),
        Department(name="Marketing", description="Brand and growth marketing"),
        Department(name="Operations", description="Business operations and logistics"),
    ]
    db.session.add_all(departments)
    db.session.flush()  # Flush to get department IDs

    # --- Seed Sample Employees ---
    from datetime import date
    employees = [
        Employee(first_name="Alice", last_name="Johnson", email="alice.johnson@enterprise.local",
                 phone="555-0101", job_title="Senior Engineer", salary=95000,
                 hire_date=date(2021, 3, 15), department_id=departments[0].id),
        Employee(first_name="Bob", last_name="Smith", email="bob.smith@enterprise.local",
                 phone="555-0102", job_title="HR Manager", salary=78000,
                 hire_date=date(2020, 7, 1), department_id=departments[1].id),
        Employee(first_name="Carol", last_name="Williams", email="carol.williams@enterprise.local",
                 phone="555-0103", job_title="Financial Analyst", salary=82000,
                 hire_date=date(2022, 1, 10), department_id=departments[2].id),
        Employee(first_name="David", last_name="Brown", email="david.brown@enterprise.local",
                 phone="555-0104", job_title="Marketing Lead", salary=88000,
                 hire_date=date(2019, 11, 20), department_id=departments[3].id),
        Employee(first_name="Eva", last_name="Davis", email="eva.davis@enterprise.local",
                 phone="555-0105", job_title="DevOps Engineer", salary=92000,
                 hire_date=date(2021, 6, 5), department_id=departments[0].id),
        Employee(first_name="Frank", last_name="Miller", email="frank.miller@enterprise.local",
                 phone="555-0106", job_title="Operations Manager", salary=87000,
                 hire_date=date(2018, 4, 3), department_id=departments[4].id),
    ]
    db.session.add_all(employees)
    db.session.commit()
