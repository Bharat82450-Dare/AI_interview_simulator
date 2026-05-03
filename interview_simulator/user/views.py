# -*- coding: utf-8 -*-
"""User views."""

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)


from interview_simulator.extensions import db
from interview_simulator.user.models import UserFile

from .forms import UploadForm
from .services import chat_gpt, gpt_questions, transcribe_audio_with_gemini

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


def _extract_pdf_text(file_storage):
    """Extract text from an uploaded resume PDF without persisting the file."""
    from pypdf import PdfReader

    file_storage.stream.seek(0)
    reader = PdfReader(file_storage.stream)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page.strip() for page in pages if page.strip()).strip()


@blueprint.route("/upload", methods=["GET", "POST"])

def upload():
    """
    Handles the uploading of the Resume and Job Description files.

    Returns:
    - A string representing the HTML page displaying the form for uploading the files.
    """
    form = UploadForm()
    if form.validate_on_submit():
        resume_text = (form.resume_text.data or "").strip()
        job_description = form.job_description.data
        resume_pdf = form.resume_pdf.data

        if resume_pdf and resume_pdf.filename:
            try:
                resume_text = _extract_pdf_text(resume_pdf)
            except Exception:
                current_app.logger.exception("Failed to extract resume PDF text")
                flash(
                    "We could not read that PDF. Try a text-based PDF or paste the resume text instead.",
                    "error",
                )
                return render_template("users/upload.html", form=form)

            if not resume_text:
                flash(
                    "That PDF did not contain readable text. Paste the resume text instead.",
                    "error",
                )
                return render_template("users/upload.html", form=form)

        # Save the uploaded resume and job description to the database
        user_file = UserFile(
            file_name="Resume", file_content=resume_text
        )
        db.session.add(user_file)

        user_file = UserFile(
            file_name="Job Description", file_content=job_description
        )
        db.session.add(user_file)

        db.session.commit()

        flash("Resume and Job Description uploaded successfully!", "success")
        return redirect(url_for("user.home_logged_in"))
    return render_template("users/upload.html", form=form)


@blueprint.route("/check_uploads")

def check_uploads():
    """
    Checks if the user has uploaded a resume and job description and returns a JSON response.

    Returns:
    - A string representing the JSON response indicating if the user has uploaded the files.
    """
    latest_resume = (
        UserFile.query.filter_by(file_name="Resume")
        .order_by(UserFile.upload_date.desc())
        .first()
    )
    latest_job_description = (
        UserFile.query.filter_by(file_name="Job Description")
        .order_by(UserFile.upload_date.desc())
        .first()
    )

    if latest_resume and latest_job_description:
        return jsonify(
            {
                "uploaded": True,
                "resume": latest_resume.file_content,
                "job_description": latest_job_description.file_content,
            }
        )
    else:
        return jsonify({"uploaded": False, "resume": None, "job_description": None})


from flask import session as flask_session
from interview_simulator.user.models import InterviewSession, QuestionRecord, AnswerRecord, EvaluationScore

@blueprint.route("/start_game", methods=["POST"])

def start_game():
    """
    Starts the game by calling the gpt_questions() function and tracking the session.

    Returns:
    - A string representing the JSON response containing the interview questions.
    """
    import json
    resume = request.json.get("resume")
    job_description = request.json.get("job_description")
    
    # Create a new interview session
    interview_session = InterviewSession()
    db.session.add(interview_session)
    db.session.commit()
    flask_session['interview_session_id'] = interview_session.id
    
    questions = gpt_questions(resume, job_description)
    
    # Save the generated questions to the database
    raw_questions = questions.get("raw_questions", [])
    for q_data in raw_questions:
        target_kw = q_data.get("target_keywords", [])
        if isinstance(target_kw, list):
            target_kw = json.dumps(target_kw)
            
        q_record = QuestionRecord(
            session=interview_session,
            question_text=q_data.get("question_text", ""),
            ideal_answer=q_data.get("ideal_answer", ""),
            target_keywords=target_kw
        )
        db.session.add(q_record)
        
    db.session.commit()
    
    return jsonify(questions)


@blueprint.route("/transcribe", methods=["POST"])

def transcribe():
    """
    Transcribes an audio file, evaluates it using NLP, and returns the score and feedback.
    """
    from .services import evaluate_answer
    
    # Get the audio file from the request
    audio_file = request.files.get("audio")
    question = request.form.get("question")

    # log the audio file
    current_app.logger.info(f"Audio file: {audio_file}")

    if audio_file:
        # Extract the audio data from the file
        audio_data = audio_file.read()

        # Extract the transcribed text from the API response
        transcription = transcribe_audio_with_gemini(audio_data)

        # Retrieve the question record
        session_id = flask_session.get('interview_session_id')
        question_record = None
        if session_id:
            # Note: exact match on question_text might fail if the frontend strips trailing spaces,
            # so we use ilike or match the beginning
            question_record = QuestionRecord.query.filter(
                QuestionRecord.session_id == session_id,
                QuestionRecord.question_text.ilike(f"{question}%")
            ).first()
            
        if question_record:
            # Save the answer
            answer_record = AnswerRecord(
                question=question_record,
                user_answer_text=transcription
            )
            db.session.add(answer_record)
            db.session.flush() # get ID
            
            # evaluate
            eval_result = evaluate_answer(
                question_record.ideal_answer,
                question_record.target_keywords,
                transcription,
                question
            )
            
            # Save score
            score_record = EvaluationScore(
                answer=answer_record,
                similarity_score=eval_result["similarity_score"],
                keyword_score=eval_result["keyword_score"],
                overall_score=eval_result["overall_score"],
                feedback=eval_result["feedback"]
            )
            db.session.add(score_record)
            db.session.commit()
            
            response = eval_result["feedback"]
            return jsonify({
                "transcription": transcription, 
                "response": response, 
                "question": question,
                "scores": {
                    "similarity": round(eval_result["similarity_score"], 1),
                    "keyword": round(eval_result["keyword_score"], 1),
                    "overall": round(eval_result["overall_score"], 1)
                }
            })
        else:
            # Fallback if no session/question found
            from .services import chat_gpt
            response = chat_gpt(question, transcription)
            return jsonify(
                {"transcription": transcription, "response": response, "question": question}
            )
    else:
        # Return an error response if no audio file was provided
        return jsonify({"error": "No audio file provided"}), 400


@blueprint.route("/home_logged_in", methods=["GET", "POST"])

def home_logged_in():
    """
    Handles the home page for logged-in users.

    This function renders the home_logged_in.html template, which displays the form for inputting a message to ChatGPT.

    Returns:
    - A string representing the HTML page displaying the form for inputting a message to ChatGPT.
    """
    return render_template("users/home_logged_in.html")
