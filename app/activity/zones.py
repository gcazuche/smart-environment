"""Resolution-independent work zones for local, ephemeral observations."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, TypeVar


class BoxLike(Protocol):
    @property
    def x(self) -> int: ...

    @property
    def y(self) -> int: ...

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...


@dataclass(frozen=True, slots=True)
class PixelBounds:
    """Pixel bounds with an exclusive right and bottom edge."""

    left: int
    top: int
    right: int
    bottom: int


@dataclass(frozen=True, slots=True)
class NormalizedWorkZone:
    """Rectangle expressed as fractions of the frame width and height."""

    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        coordinates = (self.left, self.top, self.right, self.bottom)
        if not all(math.isfinite(value) for value in coordinates):
            raise ValueError("coordenadas da área devem ser finitas")
        if not 0.0 <= self.left < self.right <= 1.0:
            raise ValueError("limites horizontais devem obedecer 0 <= esquerda < direita <= 1")
        if not 0.0 <= self.top < self.bottom <= 1.0:
            raise ValueError("limites verticais devem obedecer 0 <= topo < base <= 1")

    @classmethod
    def parse(cls, raw_value: str) -> NormalizedWorkZone:
        """Parse `left,top,right,bottom` without accepting extra content."""

        parts = tuple(part.strip() for part in raw_value.split(","))
        if len(parts) != 4 or any(not part for part in parts):
            raise ValueError("área deve usar esquerda,topo,direita,base com valores de 0 a 1")
        try:
            coordinates = tuple(float(part) for part in parts)
        except ValueError as exc:
            raise ValueError("coordenadas da área devem ser números entre 0 e 1") from exc
        return cls(*coordinates)

    def as_tuple(self) -> tuple[float, float, float, float]:
        return self.left, self.top, self.right, self.bottom

    def to_pixel_bounds(self, *, frame_width: int, frame_height: int) -> PixelBounds:
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("dimensões do frame devem ser positivas")
        left = min(round(self.left * frame_width), frame_width - 1)
        top = min(round(self.top * frame_height), frame_height - 1)
        right = min(frame_width, max(left + 1, round(self.right * frame_width)))
        bottom = min(frame_height, max(top + 1, round(self.bottom * frame_height)))
        return PixelBounds(
            left,
            top,
            right,
            bottom,
        )

    def overlap_ratio(self, box: BoxLike, *, frame_width: int, frame_height: int) -> float:
        """Return how much of a detection box is covered by this zone."""

        if box.width <= 0 or box.height <= 0:
            return 0.0
        zone = self.to_pixel_bounds(frame_width=frame_width, frame_height=frame_height)
        box_right = box.x + box.width
        box_bottom = box.y + box.height
        intersection_width = max(0, min(box_right, zone.right) - max(box.x, zone.left))
        intersection_height = max(0, min(box_bottom, zone.bottom) - max(box.y, zone.top))
        return (intersection_width * intersection_height) / (box.width * box.height)


FULL_FRAME_WORK_ZONE = NormalizedWorkZone(0.0, 0.0, 1.0, 1.0)

BoxT = TypeVar("BoxT", bound=BoxLike)


def detections_in_work_zone(
    detections: Sequence[BoxT],
    work_zone: NormalizedWorkZone,
    *,
    frame_width: int,
    frame_height: int,
    minimum_overlap_ratio: float = 0.20,
) -> tuple[BoxT, ...]:
    """Select detections with enough geometric overlap; no identity is created."""

    if not math.isfinite(minimum_overlap_ratio) or not 0.0 < minimum_overlap_ratio <= 1.0:
        raise ValueError("sobreposição mínima deve estar entre 0 e 1")
    return tuple(
        detection
        for detection in detections
        if work_zone.overlap_ratio(
            detection,
            frame_width=frame_width,
            frame_height=frame_height,
        )
        >= minimum_overlap_ratio
    )
