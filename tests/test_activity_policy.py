"""Tests for the observable-activity vocabulary and initial office policy."""

from dataclasses import FrozenInstanceError, replace
from unittest import TestCase

from app.activity import (
    DEFAULT_OFFICE_COMPUTER_POLICY,
    PROHIBITED_USES,
    ActivityState,
    ActivityThresholds,
)


class ActivityPolicyTests(TestCase):
    def test_policy_exposes_exactly_the_five_approved_states(self) -> None:
        self.assertEqual(
            {state.value for state in ActivityState},
            {
                "atividade_compativel",
                "uso_celular_aparente",
                "pausa_aparente",
                "ausente",
                "inconclusivo",
            },
        )
        self.assertEqual(
            {definition.state for definition in DEFAULT_OFFICE_COMPUTER_POLICY.states},
            set(ActivityState),
        )

    def test_initial_thresholds_match_the_approved_office_experiment(self) -> None:
        thresholds = DEFAULT_OFFICE_COMPUTER_POLICY.thresholds

        self.assertEqual(thresholds.observation_window_seconds, 10.0)
        self.assertEqual(thresholds.work_evidence_ratio, 0.60)
        self.assertEqual(thresholds.phone_evidence_ratio, 0.80)
        self.assertEqual(thresholds.absence_confirmation_seconds, 3.0)
        self.assertEqual(thresholds.break_confirmation_seconds, 60.0)

    def test_phone_state_does_not_claim_distraction(self) -> None:
        definition = DEFAULT_OFFICE_COMPUTER_POLICY.definition_for(ActivityState.PHONE_USE_APPARENT)

        self.assertIn("não significa distração", definition.limitation)
        self.assertNotIn("improdut", definition.meaning.lower())

    def test_failure_is_defined_as_inconclusive_and_not_absent(self) -> None:
        inconclusive = DEFAULT_OFFICE_COMPUTER_POLICY.definition_for(ActivityState.INCONCLUSIVE)
        absent = DEFAULT_OFFICE_COMPUTER_POLICY.definition_for(ActivityState.ABSENT)

        self.assertIn("falha", " ".join(inconclusive.evidence))
        self.assertIn("nunca equivalem a ausência", absent.limitation)

    def test_policy_records_prohibited_uses(self) -> None:
        rendered = " ".join(PROHIBITED_USES)

        self.assertIn("produtividade real", rendered)
        self.assertIn("punição", rendered)
        self.assertIn("reidentificação", rendered)

    def test_thresholds_reject_unsafe_or_incoherent_values(self) -> None:
        invalid_values = (
            {"observation_window_seconds": 1.0},
            {"minimum_reliable_observation_ratio": 0.0},
            {"work_evidence_ratio": 1.1},
            {"absence_confirmation_seconds": 11.0},
            {"break_confirmation_seconds": 9.0},
        )

        for overrides in invalid_values:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                ActivityThresholds(**overrides)

    def test_policy_and_thresholds_are_immutable(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_OFFICE_COMPUTER_POLICY.version = 2  # type: ignore[misc]

        changed = replace(
            DEFAULT_OFFICE_COMPUTER_POLICY,
            version=2,
            thresholds=replace(
                DEFAULT_OFFICE_COMPUTER_POLICY.thresholds,
                break_confirmation_seconds=90.0,
            ),
        )
        self.assertEqual(changed.version, 2)
        self.assertEqual(changed.thresholds.break_confirmation_seconds, 90.0)
