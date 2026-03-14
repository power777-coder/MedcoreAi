from difflib import SequenceMatcher
import re

try:
    from rapidfuzz import fuzz
except ImportError:
    class _FuzzFallback:
        @staticmethod
        def partial_ratio(left, right):
            return int(SequenceMatcher(None, left, right).ratio() * 100)

    fuzz = _FuzzFallback()


SYMPTOM_SYNONYMS = {
    "fever": [
        "feeling hot",
        "running a temperature",
        "high temperature",
        "hot body",
    ],
    "night sweats": [
        "sweaty",
        "sweating",
        "sweating a lot",
        "sweating heavily",
        "waking up sweaty",
    ],
    "fatigue": [
        "tired",
        "very tired",
        "exhausted",
        "low energy",
    ],
    "weakness": [
        "weak",
        "feeling weak",
        "no strength",
    ],
    "shortness of breath": [
        "breathless",
        "difficulty breathing",
        "hard to breathe",
    ],
    "loss of appetite": [
        "not hungry",
        "no appetite",
        "dont feel like eating",
        "do not feel like eating",
    ],
    "dehydration": [
        "dry mouth",
        "very thirsty",
    ],
    "dizziness": [
        "lightheaded",
        "light headed",
    ],
}


def _normalize_text(value):
    return re.sub(r"[^a-z0-9\s]+", " ", value.lower()).strip()


def extract_symptoms(text, symptom_list):
    text = _normalize_text(text)
    detected = []

    for symptom in symptom_list:
        symptom_words = _normalize_text(symptom.replace("_", " "))
        synonym_phrases = SYMPTOM_SYNONYMS.get(symptom_words, [])

        # direct match
        if symptom_words in text:
            detected.append(symptom)
            continue

        if any(_normalize_text(phrase) in text for phrase in synonym_phrases):
            detected.append(symptom)
            continue

        score = fuzz.partial_ratio(symptom_words, text)

        if score > 80:
            detected.append(symptom)

    return list(set(detected))
