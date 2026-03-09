# Enterprise Employee Management Portal
## OWASP Risk Mitigation Project – Phase 1: Architecture & Design

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser)                           │
│              Bootstrap 5 + HTML + Vanilla JS                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP Requests (Session Cookie)
┌──────────────────────────▼──────────────────────────────────────┐
│                  FLASK APPLICATION LAYER                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  ┌────────┐  │
│  │ auth        │  │ dashboard   │  │ employees  │  │ files  │  │
│  │ Blueprint   │  │ Blueprint   │  │ Blueprint  │  │ Blueprint│ │
│  └─────────────┘  └─────────────┘  └────────────┘  └────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           utils.py (decorators, helpers, logging)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SQLAlchemy ORM
┌──────────────────────────▼──────────────────────────────────────┐
│               DATABASE LAYER (SQLite)                           │
│   users │ employees │ departments │ employee_files │ audit_logs │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│               FILE SYSTEM (local uploads folder)                │
│           app/static/uploads/<uuid>.<ext>                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Application Flow

```
User visits / ──► Redirect to /auth/login
                         │
                  [POST credentials]
                         │
              ┌──────────▼──────────┐
              │  Validate username  │
              │  + password hash    │
              └──────────┬──────────┘
                  PASS   │   FAIL
            ┌────────────┘   └─────────────────────┐
            │                                       │
    Set session:                          Flash error + re-render login
    user_id, username, role
            │
            ▼
    /dashboard  ◄────────────────────────────────────┐
            │                                        │
    ┌───────▼────────────────────────────────────┐   │
    │         Role-Based Routing                 │   │
    │                                            │   │
    │  ADMIN                     USER            │   │
    │  ├── View all employees    ├── View employees   │
    │  ├── Add employee          ├── Add employee │   │
    │  ├── Edit employee         ├── Edit employee│   │
    │  ├── DELETE employee       │   (no delete)  │   │
    │  ├── View salary data      │                │   │
    │  ├── Audit logs            │                │   │
    │  └── Upload/delete files   └── Upload files │   │
    └────────────────────────────────────────────┘   │
            │                                        │
    /auth/logout ──── Clear session ─────────────────┘
```

---

## 3. Routes / Endpoints

### Authentication  (`/auth`)
| Method | Endpoint        | Description                      | Access     |
|--------|-----------------|----------------------------------|------------|
| GET    | `/auth/login`   | Render login form                | Public     |
| POST   | `/auth/login`   | Process login, set session       | Public     |
| GET    | `/auth/logout`  | Clear session, redirect to login | Auth       |
| GET    | `/`             | Redirect to login or dashboard   | Public     |

### Dashboard  (`/dashboard`)
| Method | Endpoint     | Description                           | Access |
|--------|--------------|---------------------------------------|--------|
| GET    | `/`          | Main dashboard with statistics        | Auth   |
| GET    | `/dashboard` | Alias for above                       | Auth   |

### Employee Management  (`/employees`)
| Method | Endpoint                        | Description                   | Access      |
|--------|---------------------------------|-------------------------------|-------------|
| GET    | `/employees/`                   | List all employees + search   | Auth        |
| GET    | `/employees/<id>`               | View single employee profile  | Auth        |
| GET    | `/employees/add`                | Render add employee form      | Auth        |
| POST   | `/employees/add`                | Create new employee record    | Auth        |
| GET    | `/employees/<id>/edit`          | Render edit employee form     | Auth        |
| POST   | `/employees/<id>/edit`          | Update employee record        | Auth        |
| POST   | `/employees/<id>/delete`        | Soft-delete employee          | Admin Only  |

### File Management  (`/files`)
| Method | Endpoint                    | Description                   | Access |
|--------|-----------------------------|-------------------------------|--------|
| POST   | `/files/upload/<emp_id>`    | Upload file for employee      | Auth   |
| GET    | `/files/download/<file_id>` | Download/serve stored file    | Auth   |
| POST   | `/files/delete/<file_id>`   | Delete file record + storage  | Auth   |

### HTTP Error Pages
| Code | URL Pattern    | Description             |
|------|----------------|-------------------------|
| 403  | (any)          | Access Denied           |
| 404  | (any)          | Page Not Found          |
| 500  | (any)          | Internal Server Error   |

---

## 4. Database Schema

```
┌────────────────────────────────────────────────────────────────┐
│  TABLE: users                                                  │
├──────────────┬─────────────┬───────────────────────────────────┤
│  id          │ INTEGER PK  │ Auto-increment                    │
│  username    │ VARCHAR(80) │ UNIQUE, NOT NULL, indexed         │
│  email       │ VARCHAR(120)│ UNIQUE, NOT NULL                  │
│  password_hash│ VARCHAR(256)│ Werkzeug hash, NOT NULL          │
│  role        │ VARCHAR(20) │ 'admin' | 'user', default 'user'  │
│  is_active   │ BOOLEAN     │ Default TRUE                      │
│  created_at  │ DATETIME    │ Auto UTC timestamp                │
│  last_login  │ DATETIME    │ Nullable                          │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  TABLE: departments                                            │
├──────────────┬─────────────┬───────────────────────────────────┤
│  id          │ INTEGER PK  │                                   │
│  name        │ VARCHAR(100)│ UNIQUE, NOT NULL                  │
│  description │ TEXT        │ Nullable                          │
│  created_at  │ DATETIME    │ Auto UTC timestamp                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  TABLE: employees                                              │
├──────────────┬─────────────┬───────────────────────────────────┤
│  id          │ INTEGER PK  │                                   │
│  first_name  │ VARCHAR(80) │ NOT NULL                          │
│  last_name   │ VARCHAR(80) │ NOT NULL                          │
│  email       │ VARCHAR(120)│ UNIQUE, NOT NULL, indexed         │
│  phone       │ VARCHAR(20) │ Nullable                          │
│  job_title   │ VARCHAR(100)│ Nullable                          │
│  salary      │ FLOAT       │ Nullable (sensitive field)        │
│  hire_date   │ DATE        │ Nullable                          │
│  is_active   │ BOOLEAN     │ Default TRUE (soft delete flag)   │
│  created_at  │ DATETIME    │ Auto UTC timestamp                │
│  updated_at  │ DATETIME    │ Auto-updated on change            │
│  department_id│ INTEGER FK │ → departments.id                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  TABLE: employee_files                                         │
├──────────────┬─────────────┬───────────────────────────────────┤
│  id          │ INTEGER PK  │                                   │
│  filename    │ VARCHAR(256)│ UUID-based stored name            │
│  original_filename│ VARCHAR│ User-provided filename            │
│  file_type   │ VARCHAR(50) │ Extension (pdf, png, etc.)        │
│  file_size   │ INTEGER     │ Bytes                             │
│  uploaded_at │ DATETIME    │ Auto UTC timestamp                │
│  employee_id │ INTEGER FK  │ → employees.id (CASCADE DELETE)   │
│  uploaded_by │ INTEGER FK  │ → users.id                        │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  TABLE: audit_logs                                             │
├──────────────┬─────────────┬───────────────────────────────────┤
│  id          │ INTEGER PK  │                                   │
│  user_id     │ INTEGER FK  │ → users.id (Nullable)             │
│  action      │ VARCHAR(100)│ e.g. LOGIN, CREATE_EMPLOYEE       │
│  resource    │ VARCHAR(100)│ e.g. 'employee', 'auth'           │
│  resource_id │ INTEGER     │ Nullable                          │
│  ip_address  │ VARCHAR(45) │ IPv4 or IPv6                      │
│  status      │ VARCHAR(20) │ 'success' | 'failure'             │
│  details     │ TEXT        │ Additional context                │
│  timestamp   │ DATETIME    │ Auto UTC timestamp                │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. Project Folder Structure

```
emp-portal/
│
├── run.py                          # Application entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker config (Phase 3+)
├── .gitignore
│
├── instance/                       # SQLite DB (git-ignored)
│   └── emp_portal.db
│
├── app/
│   ├── __init__.py                 # Application factory (create_app)
│   ├── utils.py                    # Decorators, access control helpers
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py             # SQLAlchemy models + init_db + seed
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                 # /auth/login, /auth/logout
│   │   ├── dashboard.py            # / and /dashboard
│   │   ├── employees.py            # /employees/* CRUD
│   │   ├── files.py                # /files/* upload/download/delete
│   │   └── errors.py               # 403, 404, 500 handlers
│   │
│   ├── templates/
│   │   ├── base.html               # Shared layout (topbar, sidebar)
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── dashboard/
│   │   │   └── index.html
│   │   ├── employees/
│   │   │   ├── list.html
│   │   │   ├── view.html
│   │   │   └── form.html           # Shared add/edit form
│   │   └── errors/
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   └── static/
│       ├── css/                    # Custom stylesheets (optional)
│       ├── js/                     # Custom scripts (optional)
│       └── uploads/                # Uploaded employee files (git-ignored)
│
├── tests/
│   └── (Phase 2: unit + integration tests)
│
└── docs/
    └── ARCHITECTURE.md             # This document
```

---

## 6. Access Control Matrix

| Feature                  | Admin | User |
|--------------------------|-------|------|
| Login / Logout           | ✅    | ✅   |
| View Dashboard           | ✅    | ✅   |
| View Audit Logs          | ✅    | ❌   |
| View Employee List       | ✅    | ✅   |
| View Employee Profile    | ✅    | ✅   |
| View Salary Data         | ✅    | ❌   |
| Add Employee             | ✅    | ✅   |
| Edit Employee            | ✅    | ✅   |
| **Delete Employee**      | ✅    | ❌   |
| Upload Files             | ✅    | ✅   |
| Download Files           | ✅    | ✅   |
| Delete Files             | ✅    | ✅   |

---

## 7. Default Seed Credentials

| Username | Password     | Role  |
|----------|--------------|-------|
| admin    | Admin@1234   | admin |
| jdoe     | User@1234    | user  |

> ⚠️ Change all credentials before any non-local deployment.

---

## 8. OWASP Phase Mapping

The following table maps intentional design points to OWASP Top 10 categories
that will be analyzed and hardened in Phase 2 and Phase 3.

| OWASP Category                          | Phase 1 Design Point                     |
|-----------------------------------------|------------------------------------------|
| A01 – Broken Access Control             | Role check via session, no CSRF token    |
| A02 – Cryptographic Failures            | SQLite in cleartext, salary exposed      |
| A03 – Injection                         | SQLAlchemy ORM used (parameterized)      |
| A04 – Insecure Design                   | Search and file features to be reviewed  |
| A05 – Security Misconfiguration         | Debug mode, dev secret key in config     |
| A06 – Vulnerable Components             | To be audited in CI/CD phase             |
| A07 – Auth & Session Failures           | Basic session, no timeout, no MFA        |
| A08 – Software Integrity                | No dependency pinning or SCA yet         |
| A09 – Logging & Monitoring              | AuditLog table exists, needs hardening   |
| A10 – SSRF                              | File upload path traversal to review     |

---

## 9. Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python run.py

# 4. Open in browser
   http://127.0.0.1:5000
   Login: admin / Admin@1234
```
