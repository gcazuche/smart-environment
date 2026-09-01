"""Observable-activity contracts for the Smart Environment prototype."""

from app.activity.policy import (
    DEFAULT_OFFICE_COMPUTER_POLICY,
    PROHIBITED_USES,
    ActivityPolicy,
    ActivityState,
    ActivityStateDefinition,
    ActivityThresholds,
)
from app.activity.zones import (
    FULL_FRAME_WORK_ZONE,
    NormalizedWorkZone,
    PixelBounds,
    detections_in_work_zone,
)

__all__ = [
    "ActivityPolicy",
    "ActivityState",
    "ActivityStateDefinition",
    "ActivityThresholds",
    "DEFAULT_OFFICE_COMPUTER_POLICY",
    "FULL_FRAME_WORK_ZONE",
    "NormalizedWorkZone",
    "PixelBounds",
    "PROHIBITED_USES",
    "detections_in_work_zone",
]
