# -*- coding: utf-8 -*-
"""User views."""

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask import session as flask_session

from interview_simulator.extensions import csrf_protect, db
from interview_simulator.user.models import (
    AnswerRecord,
    EvaluationScore,
    InterviewSession,
    QuestionRecord,
    UserFile,
)

from .services import gpt_questions, transcribe_audio_with_gemini

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/upload", methods=["GET", "POST"])
def upload():
    """Legacy simulator setup route redirected to the main product."""
    return redirect(url_for("user.prep_copilot"))


@blueprint.route("/check_uploads")
def check_uploads():
    """Return the latest uploaded simulator context if it exists."""
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
    return jsonify({"uploaded": False, "resume": None, "job_description": None})


@blueprint.route("/start_game", methods=["POST"])
def start_game():
    """Legacy simulator endpoint retained for compatibility."""
    import json

    resume = request.json.get("resume")
    job_description = request.json.get("job_description")

    interview_session = InterviewSession()
    db.session.add(interview_session)
    db.session.commit()
    flask_session["interview_session_id"] = interview_session.id

    questions = gpt_questions(resume, job_description)

    raw_questions = questions.get("raw_questions", [])
    for q_data in raw_questions:
        target_kw = q_data.get("target_keywords", [])
        if isinstance(target_kw, list):
            target_kw = json.dumps(target_kw)

        q_record = QuestionRecord(
            session=interview_session,
            question_text=q_data.get("question_text", ""),
            ideal_answer=q_data.get("ideal_answer", ""),
            target_keywords=target_kw,
        )
        db.session.add(q_record)

    db.session.commit()
    return jsonify(questions)


@blueprint.route("/transcribe", methods=["POST"])
def transcribe():
    """Legacy simulator endpoint retained for compatibility."""
    from .services import chat_gpt, evaluate_answer

    audio_file = request.files.get("audio")
    question = request.form.get("question")

    current_app.logger.info("Audio file: %s", audio_file)

    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400

    audio_data = audio_file.read()
    transcription = transcribe_audio_with_gemini(audio_data)

    session_id = flask_session.get("interview_session_id")
    question_record = None
    if session_id:
        question_record = QuestionRecord.query.filter(
            QuestionRecord.session_id == session_id,
            QuestionRecord.question_text.ilike(f"{question}%"),
        ).first()

    if not question_record:
        response = chat_gpt(question, transcription)
        return jsonify(
            {"transcription": transcription, "response": response, "question": question}
        )

    answer_record = AnswerRecord(
        question=question_record,
        user_answer_text=transcription,
    )
    db.session.add(answer_record)
    db.session.flush()

    eval_result = evaluate_answer(
        question_record.ideal_answer,
        question_record.target_keywords,
        transcription,
        question,
    )

    score_record = EvaluationScore(
        answer=answer_record,
        similarity_score=eval_result["similarity_score"],
        keyword_score=eval_result["keyword_score"],
        overall_score=eval_result["overall_score"],
        feedback=eval_result["feedback"],
    )
    db.session.add(score_record)
    db.session.commit()

    return jsonify(
        {
            "transcription": transcription,
            "response": eval_result["feedback"],
            "question": question,
            "scores": {
                "similarity": round(eval_result["similarity_score"], 1),
                "keyword": round(eval_result["keyword_score"], 1),
                "overall": round(eval_result["overall_score"], 1),
            },
        }
    )


@blueprint.route("/home_logged_in", methods=["GET", "POST"])
def home_logged_in():
    """Legacy simulator route redirected to the main product."""
    return redirect(url_for("user.prep_copilot"))


@blueprint.route("/prep_copilot", methods=["GET"])
def prep_copilot():
    """Render the main interview preparation workspace."""
    return render_template("users/prep_copilot.html")


@blueprint.route("/nlp_lab", methods=["GET"])
def nlp_lab():
    """Legacy route retained as a redirect to the product page."""
    return redirect(url_for("user.prep_copilot"))


@blueprint.route("/prep_copilot/chat", methods=["POST"])
@blueprint.route("/nlp_lab/detect_intent", methods=["POST"])
@csrf_protect.exempt
def prep_copilot_chat():
    """API endpoint for intent-aware prep chat."""
    from .nlp_lab_service import detect_intent

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    result = detect_intent(text)
    return jsonify(result)


@blueprint.route("/prep_copilot/summarize", methods=["POST"])
@blueprint.route("/nlp_lab/summarize", methods=["POST"])
@csrf_protect.exempt
def prep_copilot_summarize():
    """API endpoint for dual-model role brief summarization."""
    from .nlp_lab_service import summarize_text

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    bart_params = data.get("bart_params", {})
    t5_params = data.get("t5_params", {})
    result = summarize_text(text, bart_params=bart_params, t5_params=t5_params)
    if result:
        return jsonify(result)
    return jsonify({"error": "Failed to summarize text. Check server logs."}), 500


@blueprint.route("/prep_copilot/sample_brief", methods=["GET"])
@blueprint.route("/nlp_lab/sample_article", methods=["GET"])
def prep_copilot_sample_brief():
    """Return a realistic interview-prep source text for one-click demo."""
    article = (
        "BrightPath Analytics is hiring a junior data analyst to support product, "
        "marketing, and operations teams with reporting, dashboard maintenance, and "
        "ad hoc analysis. The role requires strong SQL skills, comfort with "
        "spreadsheets, and the ability to translate messy business questions into "
        "clear metrics. Candidates should be able to clean data, investigate trends, "
        "and present concise findings to non-technical stakeholders. Experience with "
        "Python, Tableau or Power BI, and A/B testing is preferred. The ideal "
        "candidate is organized, curious, and comfortable working across multiple "
        "teams in a fast-moving environment. Responsibilities include creating weekly "
        "performance summaries, monitoring funnel conversion metrics, identifying "
        "anomalies in campaign or revenue data, and partnering with managers to "
        "improve decision making. Applicants should prepare examples that show "
        "ownership, analytical thinking, and the ability to communicate insights with "
        "measurable business impact."
    )
    return jsonify({"article": article, "word_count": len(article.split())})
