# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from sqlalchemy.ext.hybrid import hybrid_property

from interview_simulator.database import (
    Column,
    PkModel,
    db,
    reference_col,
    relationship,
)


class UserFile(PkModel):
    """Resume and Job Description for a user."""

    __tablename__ = "user_files"
    file_name = Column(db.String(128), nullable=False)
    file_content = Column(db.Text, nullable=False)
    upload_date = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    def __init__(self, file_name, file_content, **kwargs):
        """
        Initializes a new instance of the UserFile.
        """
        super(UserFile, self).__init__(**kwargs)
        self.file_name = file_name
        self.file_content = file_content





class InterviewSession(PkModel):
    """A session for an interview."""
    __tablename__ = "interview_sessions"
    start_time = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

class QuestionRecord(PkModel):
    """A question generated for an interview session."""
    __tablename__ = "question_records"
    session_id = reference_col("interview_sessions", nullable=False)
    session = relationship("InterviewSession", backref="questions")
    question_text = Column(db.Text, nullable=False)
    ideal_answer = Column(db.Text, nullable=True)
    target_keywords = Column(db.Text, nullable=True)

class AnswerRecord(PkModel):
    """A user's answer to a question."""
    __tablename__ = "answer_records"
    question_id = reference_col("question_records", nullable=False)
    question = relationship("QuestionRecord", backref="answers")
    user_answer_text = Column(db.Text, nullable=False)

class EvaluationScore(PkModel):
    """Scores for an answer."""
    __tablename__ = "evaluation_scores"
    answer_id = reference_col("answer_records", nullable=False)
    answer = relationship("AnswerRecord", backref="score", uselist=False)
    similarity_score = Column(db.Float, nullable=True)
    keyword_score = Column(db.Float, nullable=True)
    overall_score = Column(db.Float, nullable=True)
    feedback = Column(db.Text, nullable=True)
