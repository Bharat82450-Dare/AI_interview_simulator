# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional


class UploadForm(FlaskForm):
    """Upload form."""

    resume_text = TextAreaField("Resume Text", validators=[Optional()])
    resume_pdf = FileField("Resume PDF", validators=[FileAllowed(["pdf"], "PDF files only.")])
    job_description = TextAreaField("Job Description", validators=[DataRequired()])
    submit = SubmitField("Upload")

    def validate(self, extra_validators=None):
        """Require either pasted resume text or a resume PDF."""
        if not super().validate(extra_validators=extra_validators):
            return False

        has_resume_text = bool((self.resume_text.data or "").strip())
        has_resume_pdf = bool(self.resume_pdf.data and self.resume_pdf.data.filename)

        if has_resume_text or has_resume_pdf:
            return True

        message = "Paste resume text or upload a resume PDF."
        self.resume_text.errors.append(message)
        self.resume_pdf.errors.append(message)
        return False

