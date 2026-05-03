# -*- coding: utf-8 -*-
"""Prep copilot NLP services for intent detection and role-brief summarization."""

import os
import random
import re
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ENABLE_TRANSFORMER_INTENT = os.getenv("ENABLE_TRANSFORMER_INTENT", "").lower() in {"1", "true", "yes"}

_intent_classifier = None
_intent_classifier_ready = None
_bart_summarizer = None
_t5_summarizer = None
_SCORER = None
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has",
    "have", "if", "in", "into", "is", "it", "its", "of", "on", "or", "such", "that",
    "the", "their", "there", "this", "to", "was", "will", "with", "you", "your",
}


def _has_local_model_cache(repo_id: str) -> bool:
    """Check whether a Hugging Face model repo appears to exist in the local cache."""
    cache_root = os.getenv("HF_HUB_CACHE")
    if not cache_root:
        cache_root = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
    repo_dir = os.path.join(cache_root, "models--" + repo_id.replace("/", "--"))
    return os.path.isdir(repo_dir)


def get_intent_classifier():
    """Load or return the cached zero-shot intent classifier."""
    global _intent_classifier, _intent_classifier_ready
    if _intent_classifier_ready is False:
        return None
    if _intent_classifier is None:
        try:
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
                pipeline,
            )

            model_name = "cross-encoder/nli-distilroberta-base"
            if not _has_local_model_cache(model_name):
                _intent_classifier_ready = False
                return None
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                local_files_only=True,
            )
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                local_files_only=True,
            )
            _intent_classifier = pipeline(
                "zero-shot-classification",
                model=model,
                tokenizer=tokenizer,
            )
            _intent_classifier_ready = True
        except Exception as exc:
            print(f"[nlp_lab_service] Intent model unavailable locally: {exc}")
            _intent_classifier = None
            _intent_classifier_ready = False
    return _intent_classifier


def get_bart_summarizer():
    """Load or return the cached BART-family summarizer."""
    global _bart_summarizer
    if _bart_summarizer is None:
        model_name = "sshleifer/distilbart-cnn-12-6"
        if not _has_local_model_cache(model_name):
            return None
        from transformers import pipeline

        _bart_summarizer = pipeline(
            "summarization",
            model=model_name,
            local_files_only=True,
        )
    return _bart_summarizer


def get_t5_summarizer():
    """Load or return the cached T5 summarizer."""
    global _t5_summarizer
    if _t5_summarizer is None:
        model_name = "t5-small"
        if not _has_local_model_cache(model_name):
            return None
        from transformers import pipeline

        _t5_summarizer = pipeline(
            "summarization",
            model=model_name,
            local_files_only=True,
        )
    return _t5_summarizer


def get_rouge_scorer():
    """Load or return the cached ROUGE scorer."""
    global _SCORER
    if _SCORER is None:
        from rouge_score import rouge_scorer

        _SCORER = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    return _SCORER


INTENT_RESPONSES = {
    "Greetings": [
        "Hello. Share the role, the company context, or the prep question you want to work through.",
        "Hi there. I can help you break down a job post or sharpen your interview prep.",
        "Welcome back. Tell me what role or interview question you want to focus on.",
    ],
    "Farewell": [
        "Sounds good. Come back when you want another role brief or prep pass.",
        "See you next time. Keep the strongest talking points from this session handy.",
        "Good luck with the next step. You can return anytime to tighten the brief further.",
    ],
    "Information request": [
        "I can help with that. Share the role details or the exact question you want clarified.",
        "Send the job description or the interview concern and I will pull out the important points.",
        "Happy to help. Give me the context and I will turn it into practical prep guidance.",
    ],
    "Help/Support": [
        "I can help. Tell me whether you need role clarification, summary support, or better answer framing.",
        "No problem. Describe where you are stuck and I will help you work through it.",
        "Let us fix it. Share the issue and I will guide you toward the next useful step.",
    ],
    "General conversation": [
        "Understood. If you want, we can turn that into a concrete prep question or a short role brief.",
        "Makes sense. I can also help you extract interview themes from a longer description.",
        "Sure. If there is a role or recruiter conversation behind that, send it over and we can tighten the prep.",
    ],
}


def get_chatbot_response(intent: str) -> str:
    """Map an intent label to a product-style response."""
    responses = INTENT_RESPONSES.get(
        intent,
        ["I am not fully sure what you need yet. Rephrase it as a prep question or paste the source text."],
    )
    return random.choice(responses)


def _count_syllables(word: str) -> int:
    """Approximate syllable count for a single English word."""
    word = word.lower().strip(".,!?;:")
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_reading_ease(text: str) -> float:
    """Compute an approximate Flesch Reading Ease score."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = text.split()
    if not sentences or not words:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    asl = len(words) / len(sentences)
    asw = syllables / len(words)
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return round(max(0.0, min(100.0, score)), 1)


def readability_label(score: float) -> str:
    """Convert a Flesch score to a short label."""
    if score >= 80:
        return "Very Easy"
    if score >= 60:
        return "Standard"
    if score >= 40:
        return "Fairly Difficult"
    if score >= 20:
        return "Difficult"
    return "Very Difficult"


CANDIDATE_LABELS = [
    "Greetings",
    "Farewell",
    "Information request",
    "Help/Support",
    "General conversation",
]


def _normalize_scores(raw_scores: dict) -> list[dict]:
    """Convert raw heuristic scores into percentage scores."""
    total = sum(raw_scores.values())
    if total <= 0:
        equal_score = round(100 / len(CANDIDATE_LABELS), 2)
        return [{"label": label, "score": equal_score} for label in CANDIDATE_LABELS]
    return [
        {"label": label, "score": round((raw_scores[label] / total) * 100, 2)}
        for label in CANDIDATE_LABELS
    ]


def _fallback_detect_intent(text: str) -> dict:
    """Fast keyword-based fallback when the transformer model is unavailable."""
    lowered = text.lower()
    scores = {label: 0.05 for label in CANDIDATE_LABELS}

    keyword_groups = {
        "Greetings": ["hello", "hi", "hey", "good morning", "good evening", "greetings"],
        "Farewell": ["bye", "goodbye", "see you", "thanks, that is enough", "talk later", "farewell"],
        "Information request": [
            "what",
            "how",
            "why",
            "which",
            "can you",
            "could you",
            "tell me",
            "explain",
            "role",
            "job",
            "recruiter",
            "requirements",
            "position",
            "summary",
        ],
        "Help/Support": [
            "help",
            "support",
            "stuck",
            "issue",
            "problem",
            "fix",
            "error",
            "struggling",
            "need help",
        ],
        "General conversation": [
            "interesting",
            "okay",
            "sure",
            "sounds good",
            "nice",
            "cool",
            "understood",
        ],
    }

    for label, keywords in keyword_groups.items():
        for keyword in keywords:
            if keyword in lowered:
                scores[label] += 1.0

    if "?" in text:
        scores["Information request"] += 0.8
    if len(text.split()) <= 3 and scores["Greetings"] <= 0.05 and scores["Farewell"] <= 0.05:
        scores["General conversation"] += 0.4

    normalized_scores = _normalize_scores(scores)
    top = max(normalized_scores, key=lambda item: item["score"])
    return {
        "intent": top["label"],
        "confidence": top["score"],
        "all_scores": normalized_scores,
        "chatbot_response": get_chatbot_response(top["label"]),
    }


def detect_intent(text: str) -> dict:
    """Detect the intent of user input and return a mapped assistant reply."""
    if not text.strip():
        return {
            "intent": "None",
            "confidence": 0.0,
            "all_scores": [],
            "chatbot_response": "Type a prep question or paste a role-related request to begin.",
        }

    if not ENABLE_TRANSFORMER_INTENT:
        return _fallback_detect_intent(text)

    classifier = get_intent_classifier()
    if classifier is None:
        return _fallback_detect_intent(text)

    try:
        result = classifier(text, CANDIDATE_LABELS)
        top_intent = result["labels"][0]
        confidence = round(result["scores"][0] * 100, 2)
        all_scores = [
            {"label": label, "score": round(score * 100, 2)}
            for label, score in zip(result["labels"], result["scores"])
        ]
        all_scores.sort(key=lambda item: CANDIDATE_LABELS.index(item["label"]))

        return {
            "intent": top_intent,
            "confidence": confidence,
            "all_scores": all_scores,
            "chatbot_response": get_chatbot_response(top_intent),
        }
    except Exception as exc:
        print(f"[nlp_lab_service] Error in detect_intent: {exc}")
        return _fallback_detect_intent(text)


def _format_rouge(scores: dict) -> dict:
    """Format ROUGE results as percentages."""
    return {
        "rouge1": round(scores["rouge1"].fmeasure * 100, 2),
        "rouge2": round(scores["rouge2"].fmeasure * 100, 2),
        "rougeL": round(scores["rougeL"].fmeasure * 100, 2),
    }


def _split_sentences(text: str) -> list[str]:
    """Split text into reasonably clean sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _keyword_weights(text: str) -> dict[str, int]:
    """Build simple keyword weights from the source text."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9+\-/]*", text.lower())
    weights: dict[str, int] = {}
    for word in words:
        if word in _STOPWORDS or len(word) < 3:
            continue
        weights[word] = weights.get(word, 0) + 1
    return weights


def _sentence_score(sentence: str, weights: dict[str, int], index: int) -> float:
    """Score a sentence based on keyword coverage and position."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9+\-/]*", sentence.lower())
    if not words:
        return 0.0
    keyword_score = sum(weights.get(word, 0) for word in words)
    density_bonus = keyword_score / max(len(words), 1)
    position_bonus = max(0.0, 1.25 - (index * 0.08))
    return keyword_score + density_bonus + position_bonus


def _select_sentences(sentences: list[str], target_words: int, min_sentences: int) -> str:
    """Select the highest-value sentences while preserving original order."""
    if not sentences:
        return ""
    weights = _keyword_weights(" ".join(sentences))
    ranked = sorted(
        enumerate(sentences),
        key=lambda item: _sentence_score(item[1], weights, item[0]),
        reverse=True,
    )

    selected_indexes: list[int] = []
    total_words = 0
    for index, sentence in ranked:
        selected_indexes.append(index)
        total_words += len(sentence.split())
        if len(selected_indexes) >= min_sentences and total_words >= target_words:
            break

    if not selected_indexes:
        selected_indexes = list(range(min(len(sentences), min_sentences)))

    selected_indexes = sorted(set(selected_indexes))
    return " ".join(sentences[index] for index in selected_indexes).strip()


def _fallback_summaries(text: str, bart_cfg: dict, t5_cfg: dict) -> tuple[dict, dict]:
    """Generate two offline extractive summaries when transformer models are unavailable."""
    sentences = _split_sentences(text)
    if not sentences:
        short = text.strip()
        return (
            {"summary": short, "time": 0.01, "engine": "Offline extractive fallback"},
            {"summary": short, "time": 0.01, "engine": "Offline extractive fallback"},
        )

    total_words = len(text.split())
    detailed_target = min(max(bart_cfg["min_length"], int(total_words * 0.45)), bart_cfg["max_length"])
    concise_target = min(max(t5_cfg["min_length"], int(total_words * 0.22)), t5_cfg["max_length"])

    detailed = _select_sentences(sentences, target_words=detailed_target, min_sentences=min(3, len(sentences)))
    concise = _select_sentences(sentences, target_words=concise_target, min_sentences=1)

    if concise == detailed and len(sentences) > 1:
        concise = " ".join(sentences[: min(2, len(sentences))]).strip()

    return (
        {"summary": detailed or text.strip(), "time": 0.01, "engine": "Offline extractive fallback"},
        {"summary": concise or text.strip(), "time": 0.01, "engine": "Offline extractive fallback"},
    )


def summarize_text(
    text: str,
    bart_params: dict = None,
    t5_params: dict = None,
) -> dict | None:
    """Summarize source text with BART and T5 and return a comparison payload."""
    if not text.strip():
        return None

    def _merge(defaults, overrides):
        result = dict(defaults)
        if overrides:
            for key in ("max_length", "min_length", "num_beams"):
                if key in overrides and overrides[key] is not None:
                    result[key] = int(overrides[key])
        return result

    bart_cfg = _merge({"max_length": 130, "min_length": 30, "num_beams": 4}, bart_params)
    t5_cfg = _merge({"max_length": 130, "min_length": 30, "num_beams": 4}, t5_params)

    try:
        bart = get_bart_summarizer()
        t5 = get_t5_summarizer()
        scorer = get_rouge_scorer()
        used_fallback = bart is None or t5 is None

        if used_fallback:
            bart_result, t5_result = _fallback_summaries(text, bart_cfg, t5_cfg)
            bart_summary = bart_result["summary"]
            t5_summary = t5_result["summary"]
            bart_time = bart_result["time"]
            t5_time = t5_result["time"]
            bart_engine = bart_result["engine"]
            t5_engine = t5_result["engine"]
        else:
            start_time = time.time()
            bart_out = bart(
                text,
                max_length=bart_cfg["max_length"],
                min_length=bart_cfg["min_length"],
                num_beams=bart_cfg["num_beams"],
                do_sample=False,
            )
            bart_summary = bart_out[0]["summary_text"]
            bart_time = round(time.time() - start_time, 2)
            bart_engine = "sshleifer/distilbart-cnn-12-6"

            start_time = time.time()
            t5_out = t5(
                "summarize: " + text,
                max_length=t5_cfg["max_length"],
                min_length=t5_cfg["min_length"],
                num_beams=t5_cfg["num_beams"],
                do_sample=False,
            )
            t5_summary = t5_out[0]["summary_text"]
            t5_time = round(time.time() - start_time, 2)
            t5_engine = "t5-small"

        bart_rouge_vs_orig = _format_rouge(scorer.score(text, bart_summary))
        t5_rouge_vs_orig = _format_rouge(scorer.score(text, t5_summary))
        cross_rouge_bart_as_ref = _format_rouge(scorer.score(bart_summary, t5_summary))

        bart_fre = flesch_reading_ease(bart_summary)
        t5_fre = flesch_reading_ease(t5_summary)
        orig_fre = flesch_reading_ease(text)

        analysis = _generate_analysis(
            bart_summary,
            t5_summary,
            bart_rouge_vs_orig,
            t5_rouge_vs_orig,
            bart_fre,
            t5_fre,
            bart_time,
            t5_time,
        )

        return {
            "original_length": len(text.split()),
            "original_readability": orig_fre,
            "bart": {
                "summary": bart_summary,
                "length": len(bart_summary.split()),
                "time": bart_time,
                "rouge": bart_rouge_vs_orig,
                "readability_score": bart_fre,
                "readability_label": readability_label(bart_fre),
                "params": bart_cfg,
                "engine": bart_engine,
            },
            "t5": {
                "summary": t5_summary,
                "length": len(t5_summary.split()),
                "time": t5_time,
                "rouge": t5_rouge_vs_orig,
                "readability_score": t5_fre,
                "readability_label": readability_label(t5_fre),
                "params": t5_cfg,
                "engine": t5_engine,
            },
            "cross_rouge": cross_rouge_bart_as_ref,
            "analysis": analysis,
            "used_fallback": used_fallback,
        }
    except Exception as exc:
        print(f"[nlp_lab_service] Error in summarize_text: {exc}")
        return None


def _winner(a, b, a_label="BART", b_label="T5", higher_is_better=True):
    """Return the label of the better-performing model."""
    if higher_is_better:
        return a_label if a >= b else b_label
    return a_label if a <= b else b_label


def _generate_analysis(
    bart_summary,
    t5_summary,
    bart_rouge,
    t5_rouge,
    bart_fre,
    t5_fre,
    bart_time,
    t5_time,
) -> dict:
    """Build a structured analysis dictionary for the UI and rubric outputs."""
    rouge_winner = _winner(bart_rouge["rouge1"], t5_rouge["rouge1"])
    speed_winner = _winner(bart_time, t5_time, higher_is_better=False)
    read_winner = _winner(bart_fre, t5_fre)
    length_diff = abs(len(bart_summary.split()) - len(t5_summary.split()))
    rouge_leader = bart_rouge["rouge1"] if rouge_winner == "BART" else t5_rouge["rouge1"]
    rouge_laggard = t5_rouge["rouge1"] if rouge_winner == "BART" else bart_rouge["rouge1"]

    observations = [
        f"**Coverage:** {rouge_winner} retained more source detail by ROUGE-1 ({rouge_leader:.1f}% vs {rouge_laggard:.1f}%). That usually means stronger overlap with the original job brief.",
        f"**Speed:** {speed_winner} returned faster ({min(bart_time, t5_time):.2f}s vs {max(bart_time, t5_time):.2f}s), which matters when users are iterating through several role descriptions.",
        f"**Readability:** {read_winner} produced the easier-to-scan output (Flesch {max(bart_fre, t5_fre):.1f} vs {min(bart_fre, t5_fre):.1f}).",
        f"**Length:** The two summaries differ by about {length_diff} words. {'BART keeps more detail for deeper review.' if len(bart_summary.split()) > len(t5_summary.split()) else 'T5 is more concise for quick scanning.'}",
        "**Variation:** The summaries phrase the same source differently, which is useful when choosing between depth and brevity.",
    ]

    limitations = {
        "BART": [
            "The detailed summary can be longer than necessary for a quick recruiter screen.",
            "Longer outputs can occasionally include extra wording that is not essential to the prep task.",
            "This model is heavier and can take longer to respond on limited hardware.",
        ],
        "T5": [
            "The concise summary may skip nuance that matters for deeper interview preparation.",
            "It depends on the summarize prefix convention, which can feel rigid in custom workflows.",
            "Shorter outputs may underplay tools, constraints, or stakeholder context in technical roles.",
        ],
    }

    applicability = [
        "**Job Description Review:** Use the detailed brief when you want stronger retention of responsibilities, tools, and qualifications.",
        "**Recruiter Call Prep:** Use the concise brief when you need a fast, scannable version before a conversation.",
        "**Company Research Notes:** Run long company or team descriptions through both models and keep the one that balances speed with clarity.",
        "**Interview Planning:** Compare the two summaries to decide whether your prep needs more coverage or more brevity.",
    ]

    overall_winner = rouge_winner
    conclusion = (
        f"On this input, **{overall_winner}** leads on source coverage. In practice, choose the detailed brief when retention matters most and the concise brief when speed and scanability matter more."
    )

    return {
        "observations": observations,
        "limitations": limitations,
        "applicability": applicability,
        "conclusion": conclusion,
        "rouge_winner": rouge_winner,
        "speed_winner": speed_winner,
        "read_winner": read_winner,
    }
