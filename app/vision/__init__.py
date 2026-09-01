"""Computer-vision contracts and implementations."""

from app.vision.intel_person import IntelPersonDetector, IntelPersonModelError
from app.vision.intel_yolo import IntelYoloModelError
from app.vision.nanodet_person import NanoDetModelError, NanoDetPersonDetector
from app.vision.office_objects import (
    OFFICE_OBJECT_CLASSES,
    IntelOfficeObjectDetector,
    OfficeObjectDetection,
)
from app.vision.person_detection import (
    Detection,
    HogPersonDetector,
    HybridPersonDetector,
    PersonDetector,
)

__all__ = [
    "Detection",
    "HogPersonDetector",
    "HybridPersonDetector",
    "IntelPersonDetector",
    "IntelPersonModelError",
    "IntelOfficeObjectDetector",
    "IntelYoloModelError",
    "NanoDetModelError",
    "NanoDetPersonDetector",
    "OFFICE_OBJECT_CLASSES",
    "OfficeObjectDetection",
    "PersonDetector",
]
