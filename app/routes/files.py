"""
File Upload Routes
Handles uploading, listing, and downloading employee documents.
NOTE: Phase 2 will demonstrate file upload vulnerabilities and mitigations.
"""

import os
import uuid
from flask import Blueprint, request, redirect, url_for, flash, send_from_directory, current_app
from app.models.database import db, Employee, EmployeeFile
from app.utils import login_required, get_current_user, log_action

files_bp = Blueprint("files", __name__, url_prefix="/files")


def allowed_file(filename):
    """Check if the file extension is in the allowed set."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", set())
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# -----------------------------------------------------------------------------
# UPLOAD FILE FOR EMPLOYEE
# -----------------------------------------------------------------------------
@files_bp.route("/upload/<int:employee_id>", methods=["POST"])
@login_required
def upload_file(employee_id):
    """
    POST /files/upload/<employee_id>
    Upload a document or profile file for the given employee.
    """
    employee = Employee.query.get_or_404(employee_id)
    current_user = get_current_user()

    if "file" not in request.files:
        flash("No file part in the request.", "danger")
        return redirect(url_for("employees.view_employee", employee_id=employee_id))

    file = request.files["file"]

    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("employees.view_employee", employee_id=employee_id))

    if file and allowed_file(file.filename):
        original_filename = file.filename
        extension = original_filename.rsplit(".", 1)[1].lower()
        # Generate a unique filename to avoid collisions
        stored_filename = f"{uuid.uuid4().hex}.{extension}"

        upload_path = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, stored_filename))

        file_record = EmployeeFile(
            filename=stored_filename,
            original_filename=original_filename,
            file_type=extension,
            file_size=os.path.getsize(os.path.join(upload_path, stored_filename)),
            employee_id=employee_id,
            uploaded_by=current_user.id,
        )
        db.session.add(file_record)
        db.session.commit()

        log_action("UPLOAD_FILE", resource="employee_file", resource_id=file_record.id,
                   details=f"File '{original_filename}' uploaded for employee {employee_id}")
        flash(f"File '{original_filename}' uploaded successfully.", "success")
    else:
        flash("File type not allowed. Permitted: pdf, png, jpg, jpeg, doc, docx", "danger")

    return redirect(url_for("employees.view_employee", employee_id=employee_id))


# -----------------------------------------------------------------------------
# DOWNLOAD / SERVE FILE
# -----------------------------------------------------------------------------
@files_bp.route("/download/<int:file_id>")
@login_required
def download_file(file_id):
    """
    GET /files/download/<file_id>
    Serve a stored file for download.
    """
    file_record = EmployeeFile.query.get_or_404(file_id)
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    log_action("DOWNLOAD_FILE", resource="employee_file", resource_id=file_id)
    return send_from_directory(
        upload_folder,
        file_record.filename,
        as_attachment=True,
        download_name=file_record.original_filename,
    )


# -----------------------------------------------------------------------------
# DELETE FILE (Admin Only shown, but any logged-in user for now)
# -----------------------------------------------------------------------------
@files_bp.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    """
    POST /files/delete/<file_id>
    Remove a file record and the stored file.
    """
    file_record = EmployeeFile.query.get_or_404(file_id)
    employee_id = file_record.employee_id
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # Remove physical file
    file_path = os.path.join(upload_folder, file_record.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(file_record)
    db.session.commit()

    log_action("DELETE_FILE", resource="employee_file", resource_id=file_id)
    flash("File deleted successfully.", "info")
    return redirect(url_for("employees.view_employee", employee_id=employee_id))
