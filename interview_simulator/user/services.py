# -*- coding: utf-8 -*-
"""Services for the user app."""
import base64
import os
import re
from io import BytesIO

from google.cloud import texttospeech
import google.generativeai as genai
from flask import current_app

def _get_model(json_mode=False):
    """Internal helper to get the Gemini model with optional JSON mode."""
    genai.configure(api_key=current_app.config["GOOGLE_API_KEY"])
    model_name = current_app.config["GEMINI_MODEL"]
    if json_mode:
        return genai.GenerativeModel(
            model_name, 
            generation_config={"response_mime_type": "application/json"}
        )
    return genai.GenerativeModel(model_name)


def read_file(file_path):
    """
    Reads the contents of a file and returns them as a string.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The contents of the file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def chat_gpt(question, answer):
    """
    Sends a message to Gemini and returns the response.
    
    Provides constructive criticism to people answering interview questions,
    using the STAR method.
    """

    system_message = """
    You are JudgeGPT. You provide constructive criticism to people who are answering interview questions. Be detailed and encouraging. Describe how to use the STAR method every time you reference it.
    """
    intro_example = read_file("interview_simulator/user/prompts/intro_example.txt")
    star_example = read_file("interview_simulator/user/prompts/star_example.txt")
    
    model = _get_model()
    prompt = f"{system_message}\n\nExample Feedback:\n{intro_example}\n{star_example}\n\nQuestion: {question}\nUser Answer: {answer}\n\nProvide your feedback now:"
    
    response = model.generate_content(prompt)
    return response.text.strip()


def gpt_questions(resume, job_description):
    """
    Uses Gemini to generate interview questions for a job candidate.
    """
    import json
    system_message = """
    You are a Hiring Manager named Alex. Generate 3 interview questions related to both the job description and the candidate's resume.
    For each question, also generate an ideal answer and a list of target keywords that should be present in a good answer.

    Return the result in this JSON structure:
    {
      "intro": "introductory text from Alex",
      "questions": [
        {
          "question_text": "the question",
          "ideal_answer": "the ideal answer",
          "target_keywords": ["keyword1", "keyword2"]
        }
      ]
    }
    """
    
    model = _get_model(json_mode=True)
    prompt = f"{system_message}\n\nCandidate Resume:\n{resume}\n\nJob Description:\n{job_description}"
    
    response = model.generate_content(prompt)
    
    try:
        data = json.loads(response.text.strip())
    except Exception as e:
        print("Failed to parse Gemini JSON", e)
        data = {
            "intro": "Hello, I am Alex. To start us off, tell me a bit about yourself.",
            "questions": [
                {"question_text": "Tell me about your experience.", "ideal_answer": "Relevant experience.", "target_keywords": ["experience"]},
                {"question_text": "What is your biggest strength?", "ideal_answer": "Hard worker.", "target_keywords": ["strength"]},
                {"question_text": "Why do you want this job?", "ideal_answer": "Great fit.", "target_keywords": ["fit"]}
            ]
        }

    intro = data.get("intro", "") + " To start us off, tell me a bit about yourself."
    intro_a = text_to_speech(intro)
    
    questions_data = data.get("questions", [])
    result = {
        "intro": intro,
        "intro_audio": intro_a,
        "raw_questions": questions_data
    }
    
    for i, q in enumerate(questions_data[:3]):
        q_text = q.get("question_text", "")
        result[f"question_{i+1}"] = q_text
        result[f"question_{i+1}_audio"] = text_to_speech(q_text)
        
    return result


def text_to_speech(text):
    """

    Uses Google Cloud Text-to-Speech to convert the input text into # noqa
    speech and returns the audio data in base64 encoded format.

    Args:
    - text (str): The text to convert into speech.

    Returns:
    - A base64 encoded string containing the audio data of the synthesized speech.

    Example Usage:
    ```
    speech = text_to_speech("Hello, world!")
    print(speech)
    ```
    """
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name="en-US-Neural2-J"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    return base64.b64encode(response.audio_content).decode("utf-8")


class NamedBytesIO(BytesIO):
    """An in-memory file-like object that has a name attribute."""

    def __init__(self, data, name):
        """Initialize the object with the given data and name."""
        super().__init__(data)
        self.name = name


def transcribe_audio_with_gemini(audio_data):
    """
    Uses Gemini to transcribe input audio data.
    """
    model = _get_model()
    
    # Prepare the audio part for Gemini
    audio_part = {
        "mime_type": "audio/webm",
        "data": audio_data
    }
    
    prompt = "Transcribe this audio clip exactly. Return only the transcription text, nothing else."
    
    response = model.generate_content([prompt, audio_part])
    return response.text.strip()

def evaluate_answer(ideal_answer, target_keywords, user_answer, question_text):
    from interview_simulator.user.nlp_engine import calculate_similarity, calculate_keyword_coverage, compute_final_score
    
    sim_score = calculate_similarity(ideal_answer, user_answer)
    kw_score = calculate_keyword_coverage(target_keywords, user_answer)
    final_score = compute_final_score(sim_score, kw_score, user_answer)
    
    feedback_prompt = f"The user answered the question '{question_text}' with: '{user_answer}'. The ideal answer is '{ideal_answer}'. The user scored {final_score:.1f}/100 based on similarity and keywords. Provide a very brief 2-sentence encouraging feedback."
    
    try:
        model = _get_model()
        response = model.generate_content(feedback_prompt)
        feedback = response.text.strip()
    except Exception as e:
        print("Failed to get Gemini feedback:", e)
        feedback = "Good effort. Keep practicing to hit more key points."
        
    return {
        "similarity_score": sim_score,
        "keyword_score": kw_score,
        "overall_score": final_score,
        "feedback": feedback
    }
