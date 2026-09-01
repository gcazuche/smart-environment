"""Tests for resolution-independent work zones."""

from unittest import TestCase

from app.activity import (
    FULL_FRAME_WORK_ZONE,
    NormalizedWorkZone,
    PixelBounds,
    detections_in_work_zone,
)
from app.vision import Detection


class WorkZoneTests(TestCase):
    def test_parses_normalized_coordinates_and_scales_to_pixels(self) -> None:
        zone = NormalizedWorkZone.parse("0.25, 0.10, 0.75, 0.90")

        self.assertEqual(zone.as_tuple(), (0.25, 0.10, 0.75, 0.90))
        self.assertEqual(
            zone.to_pixel_bounds(frame_width=200, frame_height=100),
            PixelBounds(50, 10, 150, 90),
        )

    def test_rejects_invalid_or_non_finite_coordinates(self) -> None:
        invalid_values = (
            "0,0,1",
            "0,0,0,1",
            "-0.1,0,1,1",
            "0,0,1.1,1",
            "0,0,nan,1",
            "left,0,1,1",
        )

        for raw_value in invalid_values:
            with self.subTest(raw_value=raw_value), self.assertRaises(ValueError):
                NormalizedWorkZone.parse(raw_value)

    def test_selects_detections_by_overlap_without_creating_identity(self) -> None:
        zone = NormalizedWorkZone(0.0, 0.0, 0.5, 1.0)
        inside = Detection(10, 10, 20, 40, 0.9)
        boundary = Detection(45, 10, 20, 40, 0.8)
        outside = Detection(70, 10, 20, 40, 0.7)

        selected = detections_in_work_zone(
            (inside, boundary, outside),
            zone,
            frame_width=100,
            frame_height=100,
        )

        self.assertEqual(selected, (inside, boundary))
        self.assertIs(selected[0], inside)

    def test_full_frame_zone_covers_a_valid_detection(self) -> None:
        detection = Detection(2, 3, 10, 20, 0.5)

        self.assertEqual(
            detections_in_work_zone(
                (detection,),
                FULL_FRAME_WORK_ZONE,
                frame_width=100,
                frame_height=80,
            ),
            (detection,),
        )

    def test_tiny_normalized_zone_stays_inside_a_one_pixel_frame(self) -> None:
        zone = NormalizedWorkZone(0.99, 0.99, 1.0, 1.0)

        self.assertEqual(
            zone.to_pixel_bounds(frame_width=1, frame_height=1),
            PixelBounds(0, 0, 1, 1),
        )

    def test_rejects_invalid_frame_and_overlap_parameters(self) -> None:
        with self.assertRaises(ValueError):
            FULL_FRAME_WORK_ZONE.to_pixel_bounds(frame_width=0, frame_height=100)
        with self.assertRaises(ValueError):
            detections_in_work_zone(
                (),
                FULL_FRAME_WORK_ZONE,
                frame_width=100,
                frame_height=100,
                minimum_overlap_ratio=0.0,
            )
