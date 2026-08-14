"""Computer-vision contracts and implementations."""

from app.vision.person_detection import (
    Detection,
    HogPersonDetector,
    HybridPersonDetector,
    PersonDetector,
)

__all__ = ["Detection", "HogPersonDetector", "HybridPersonDetector", "PersonDetector"]
