import os
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np


MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
DEFAULT_IMAGE_SIZE = (64, 64)
DEFAULT_CONFIDENCE_THRESHOLD = 0.45


def validate_uploaded_image(image_file):
    if not image_file:
        return "Image file is required."

    extension = os.path.splitext(image_file.name or "")[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return "Only JPG, PNG, and WEBP images are supported."

    content_type = getattr(image_file, "content_type", "")
    if content_type and content_type.lower() not in ALLOWED_IMAGE_CONTENT_TYPES:
        return "Unsupported image content type."

    if image_file.size > MAX_IMAGE_SIZE_BYTES:
        return "Image must be 5 MB or smaller."

    return None


@dataclass
class VisionPrediction:
    symptoms: list[str]
    confidence: float
    summary: str
    source: str
    raw_scores: dict[str, float]

    def to_dict(self):
        return {
            "symptoms": self.symptoms,
            "confidence": self.confidence,
            "summary": self.summary,
            "source": self.source,
            "raw_scores": self.raw_scores,
        }


class VisionModelService:
    def __init__(self):
        self.model_path = os.getenv("VISION_MODEL_PATH", "").strip()
        self.label_names = self._load_label_names()
        self.confidence_threshold = self._load_confidence_threshold()
        self.image_size = DEFAULT_IMAGE_SIZE
        self._model = None
        self._load_error = None
        self._loaded = False

    def _load_label_names(self):
        raw = os.getenv("VISION_LABELS", "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _load_confidence_threshold(self):
        raw = os.getenv("VISION_CONFIDENCE_THRESHOLD", "").strip()
        if not raw:
            return DEFAULT_CONFIDENCE_THRESHOLD
        try:
            value = float(raw)
        except ValueError:
            return DEFAULT_CONFIDENCE_THRESHOLD
        return min(max(value, 0.0), 1.0)

    def _ensure_loaded(self):
        if self._loaded:
            return

        self._loaded = True
        if not self.model_path:
            self._load_error = "VISION_MODEL_PATH is not set."
            return

        model_file = Path(self.model_path)
        if not model_file.exists():
            self._load_error = f"Vision model file was not found: {model_file}"
            return

        try:
            self._model = joblib.load(model_file)
        except Exception as exc:
            self._load_error = f"Failed to load vision model: {exc}"

    def available(self):
        self._ensure_loaded()
        return self._model is not None

    def explain_unavailable(self):
        self._ensure_loaded()
        return self._load_error or "Vision model is unavailable."

    def analyze(self, image_file):
        self._ensure_loaded()
        if not self._model:
            return VisionPrediction(
                symptoms=[],
                confidence=0.0,
                summary=self.explain_unavailable(),
                source="backend-placeholder",
                raw_scores={},
            )

        try:
            features = self._extract_features(image_file)
            score_map = self._predict_scores(features)
        except Exception as exc:
            return VisionPrediction(
                symptoms=[],
                confidence=0.0,
                summary=f"Vision inference unavailable: {exc}",
                source="backend-placeholder",
                raw_scores={},
            )

        selected = [
            symptom
            for symptom, score in sorted(score_map.items(), key=lambda item: item[1], reverse=True)
            if score >= self.confidence_threshold
        ]
        top_confidence = max(score_map.values(), default=0.0)

        if selected:
            summary = f"Detected visual symptom signals above {self.confidence_threshold:.2f} confidence."
        else:
            summary = "Image processed, but no visual symptom signal crossed the confidence threshold."

        return VisionPrediction(
            symptoms=selected,
            confidence=top_confidence,
            summary=summary,
            source="backend-model",
            raw_scores=score_map,
        )

    def _extract_features(self, image_file):
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Pillow is not installed. Install it before enabling backend image inference."
            ) from exc

        image_file.seek(0)
        with Image.open(image_file) as image:
            image = image.convert("RGB")
            image = image.resize(self.image_size)
            array = np.asarray(image, dtype=np.float32) / 255.0
        image_file.seek(0)
        return array.reshape(1, -1)

    def _predict_scores(self, features):
        model = self._model

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features)
            return self._normalize_probabilities(probabilities, model)

        if hasattr(model, "decision_function"):
            decision = model.decision_function(features)
            probabilities = 1.0 / (1.0 + np.exp(-np.asarray(decision)))
            return self._normalize_array(probabilities, model)

        if callable(model):
            result = model(features)
            if isinstance(result, dict):
                return {str(key): float(value) for key, value in result.items()}

        raise ValueError(
            "Unsupported vision model interface. Expected predict_proba, decision_function, or callable."
        )

    def _normalize_probabilities(self, probabilities, model):
        if isinstance(probabilities, list):
            scores = {}
            labels = self._resolve_labels(model, fallback_count=len(probabilities))
            for index, class_probs in enumerate(probabilities):
                label = labels[index]
                array = np.asarray(class_probs).reshape(-1)
                score = float(array[-1]) if array.size else 0.0
                scores[label] = score
            return scores

        return self._normalize_array(probabilities, model)

    def _normalize_array(self, values, model):
        array = np.asarray(values, dtype=np.float32)
        if array.ndim == 1:
            array = array.reshape(1, -1)

        labels = self._resolve_labels(model, fallback_count=array.shape[1])
        first_row = array[0]
        return {labels[index]: float(first_row[index]) for index in range(len(labels))}

    def _resolve_labels(self, model, fallback_count):
        if self.label_names:
            return self.label_names

        model_classes = getattr(model, "classes_", None)
        if model_classes is not None and not isinstance(model_classes, list):
            return [str(label) for label in np.asarray(model_classes).reshape(-1).tolist()]

        if isinstance(model_classes, list):
            labels = []
            for index, item in enumerate(model_classes):
                if isinstance(item, (list, tuple, np.ndarray)) and len(item) > 0:
                    labels.append(str(np.asarray(item).reshape(-1)[-1]))
                else:
                    labels.append(f"label_{index + 1}")
            return labels

        return [f"label_{index + 1}" for index in range(fallback_count)]


vision_service = VisionModelService()


def analyze_uploaded_image(image_file):
    return vision_service.analyze(image_file).to_dict()
