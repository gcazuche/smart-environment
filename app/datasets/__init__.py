"""Dataset preparation contracts for authorized, reproducible evaluation data."""

from app.datasets.authorized_workstations import (
    AUTHORIZED_SCENE_GROUPS,
    AUTHORIZED_SOURCE_FINGERPRINT_SHA256,
    COCO_PRELABEL_CLASSES,
    DATASET_CLASSES,
    DEFAULT_AUTHORIZED_SOURCE_DIRECTORY,
    DEFAULT_PRELABEL_OUTPUT_DIRECTORY,
    AuthorizedDatasetError,
    Prelabel,
    SceneGroup,
    prepare_authorized_workstation_prelabels,
    suppress_duplicate_prelabels,
)
from app.datasets.image_references import PinnedImageReference, validate_pinned_image_payload
from app.datasets.synthetic_workstations import (
    DEFAULT_SYNTHETIC_DIRECTORY,
    SYNTHETIC_DATASET_NAME,
    SYNTHETIC_DATASET_SOURCE,
    SYNTHETIC_DATASET_USAGE,
    SYNTHETIC_REFERENCE_IMAGES,
    SyntheticReferenceImage,
    prepare_synthetic_workstation_manifest,
)
from app.datasets.workstation_references import (
    DATASET_LICENSE,
    DATASET_LICENSE_URL,
    DATASET_REPOSITORY,
    REFERENCE_IMAGES,
    ReferenceImage,
    prepare_workstation_references,
)

__all__ = [
    "AUTHORIZED_SCENE_GROUPS",
    "AUTHORIZED_SOURCE_FINGERPRINT_SHA256",
    "COCO_PRELABEL_CLASSES",
    "DATASET_LICENSE",
    "DATASET_LICENSE_URL",
    "DATASET_REPOSITORY",
    "DATASET_CLASSES",
    "DEFAULT_AUTHORIZED_SOURCE_DIRECTORY",
    "DEFAULT_PRELABEL_OUTPUT_DIRECTORY",
    "DEFAULT_SYNTHETIC_DIRECTORY",
    "AuthorizedDatasetError",
    "PinnedImageReference",
    "Prelabel",
    "REFERENCE_IMAGES",
    "ReferenceImage",
    "SYNTHETIC_DATASET_NAME",
    "SYNTHETIC_DATASET_SOURCE",
    "SYNTHETIC_DATASET_USAGE",
    "SYNTHETIC_REFERENCE_IMAGES",
    "SyntheticReferenceImage",
    "SceneGroup",
    "prepare_authorized_workstation_prelabels",
    "prepare_synthetic_workstation_manifest",
    "prepare_workstation_references",
    "suppress_duplicate_prelabels",
    "validate_pinned_image_payload",
]
