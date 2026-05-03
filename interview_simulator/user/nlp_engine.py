# -*- coding: utf-8 -*-
"""Core NLP Evaluation Engine for the interview simulator."""
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Lazy load models to save memory during import
_spacy_nlp = None
_sentence_model = None

def get_spacy():
    global _spacy_nlp
    if _spacy_nlp is None:
        _spacy_nlp = spacy.load("en_core_web_md")
    return _spacy_nlp

def get_sentence_model():
    global _sentence_model
    if _sentence_model is None:
        _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sentence_model


def extract_skills(text):
    """
    Extract skills from resume or job description using spaCy.
    Returns a list of unique skills (nouns, proper nouns, entities).
    """
    nlp = get_spacy()
    doc = nlp(text)
    skills = set()
    
    # Extract entities that are likely skills (Organizations, Products, etc.)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "NORP", "GPE"]:
            skills.add(ent.text.lower())
    
    # Fallback to noun chunks
    for chunk in doc.noun_chunks:
        # Filter short or overly long chunks
        if 2 <= len(chunk.text) <= 30:
            skills.add(chunk.text.lower())
            
    return list(skills)


def calculate_similarity(ideal_answer, user_answer):
    """
    Calculate semantic similarity between the user's answer and the ideal answer.
    Returns a score between 0 and 100.
    """
    if not ideal_answer or not user_answer:
        return 0.0
        
    model = get_sentence_model()
    embeddings = model.encode([ideal_answer, user_answer])
    
    # Calculate cosine similarity
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    # Normalize score from [-1, 1] to [0, 100]
    score = (sim + 1) / 2 * 100
    
    # Adjust score to be more strict:
    # Sentence similarity tends to be > 0.5 for most sentences. 
    # Let's map [0.5, 1.0] to [0, 100]
    if sim < 0.2:
        return 0.0
    return min(100.0, max(0.0, (sim - 0.2) / 0.8 * 100))


def calculate_keyword_coverage(target_keywords, user_answer):
    """
    Calculate how many of the target keywords are present in the user's answer.
    Returns a score between 0 and 100.
    """
    if not target_keywords:
        return 100.0 # No keywords expected
        
    if not user_answer:
        return 0.0
        
    if isinstance(target_keywords, str):
        # Split comma separated or JSON array string
        target_keywords = [k.strip() for k in re.split(r'[,;\[\]"]+', target_keywords) if k.strip()]
        
    if not target_keywords:
        return 100.0
        
    user_answer_lower = user_answer.lower()
    
    found_count = 0
    for keyword in target_keywords:
        if keyword.lower() in user_answer_lower:
            found_count += 1
            
    return (found_count / len(target_keywords)) * 100


def compute_final_score(similarity_score, keyword_score, user_answer):
    """
    Compute a final score out of 100 based on similarity, keyword coverage, and length.
    """
    # 60% similarity, 40% keyword coverage
    base_score = (similarity_score * 0.6) + (keyword_score * 0.4)
    
    # Penalize extremely short answers (< 10 words)
    words = user_answer.split()
    if len(words) < 10:
        base_score *= (len(words) / 10.0)
        
    return min(100.0, base_score)
