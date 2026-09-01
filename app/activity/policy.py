"""Versioned contract for observable activity in an office-computer context.

This module deliberately defines vocabulary and thresholds only. It does not inspect
frames, identify people, infer intent, or calculate a productivity score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum


class ActivityState(StrEnum):
    """Stable machine values exposed by future activity observations."""

    ACTIVITY_COMPATIBLE = "atividade_compativel"
    PHONE_USE_APPARENT = "uso_celular_aparente"
    BREAK_APPARENT = "pausa_aparente"
    ABSENT = "ausente"
    INCONCLUSIVE = "inconclusivo"


@dataclass(frozen=True, slots=True)
class ActivityStateDefinition:
    """Human-readable, observable meaning of one state."""

    state: ActivityState
    label: str
    meaning: str
    evidence: tuple[str, ...]
    limitation: str


@dataclass(frozen=True, slots=True)
class ActivityThresholds:
    """Initial, configurable timing policy for a controlled TCC experiment."""

    observation_window_seconds: float = 10.0
    minimum_reliable_observation_ratio: float = 0.70
    work_evidence_ratio: float = 0.60
    phone_evidence_ratio: float = 0.80
    absence_confirmation_seconds: float = 3.0
    break_confirmation_seconds: float = 60.0

    def __post_init__(self) -> None:
        numeric_values = (
            self.observation_window_seconds,
            self.minimum_reliable_observation_ratio,
            self.work_evidence_ratio,
            self.phone_evidence_ratio,
            self.absence_confirmation_seconds,
            self.break_confirmation_seconds,
        )
        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError("limiares de atividade devem ser finitos")
        if not 2.0 <= self.observation_window_seconds <= 60.0:
            raise ValueError("janela de observação deve estar entre 2 e 60 segundos")
        for name, ratio in (
            ("observação confiável", self.minimum_reliable_observation_ratio),
            ("evidência de trabalho", self.work_evidence_ratio),
            ("evidência de celular", self.phone_evidence_ratio),
        ):
            if not 0.0 < ratio <= 1.0:
                raise ValueError(f"proporção de {name} deve estar entre 0 e 1")
        if not 0.0 < self.absence_confirmation_seconds <= self.observation_window_seconds:
            raise ValueError("confirmação de ausência deve caber na janela de observação")
        if self.break_confirmation_seconds < self.observation_window_seconds:
            raise ValueError("confirmação de pausa não pode ser menor que a janela")


PROHIBITED_USES = (
    "reconhecimento facial ou identificação individual",
    "inferência de emoção, intenção ou produtividade real",
    "pontuação, ranking ou controle de jornada",
    "punição ou decisão adversa automática",
    "reidentificação entre câmeras ou sessões",
)


_OFFICE_COMPUTER_STATES = (
    ActivityStateDefinition(
        state=ActivityState.ACTIVITY_COMPATIBLE,
        label="Atividade compatível",
        meaning="Há sinais visuais compatíveis com tarefas na estação de trabalho.",
        evidence=(
            "pessoa presente na área configurada",
            "interação sustentada com teclado, mouse, computador, documento ou ferramenta",
        ),
        limitation="Não comprova produtividade, qualidade, atenção ou intenção.",
    ),
    ActivityStateDefinition(
        state=ActivityState.PHONE_USE_APPARENT,
        label="Uso aparente de celular",
        meaning="Há interação visual sustentada com um objeto classificado como celular.",
        evidence=(
            "pessoa presente na área configurada",
            "celular detectado próximo às mãos durante a janela",
        ),
        limitation="O uso pode ser profissional; este estado não significa distração.",
    ),
    ActivityStateDefinition(
        state=ActivityState.BREAK_APPARENT,
        label="Pausa aparente",
        meaning="A pessoa permanece presente sem sinais suficientes de interação configurada.",
        evidence=(
            "pessoa presente de forma confiável",
            "ausência sustentada de sinais configurados de trabalho ou celular",
        ),
        limitation="Pensar, conversar, ler ou aguardar podem ser trabalho legítimo.",
    ),
    ActivityStateDefinition(
        state=ActivityState.ABSENT,
        label="Ausente",
        meaning="Nenhuma pessoa foi observada na área durante o tempo de confirmação.",
        evidence=(
            "câmera e detector saudáveis",
            "ausência sustentada de detecção na área configurada",
        ),
        limitation="Falha da câmera, do modelo ou baixa visibilidade nunca equivalem a ausência.",
    ),
    ActivityStateDefinition(
        state=ActivityState.INCONCLUSIVE,
        label="Inconclusivo",
        meaning="As evidências são insuficientes, conflitantes ou pouco confiáveis.",
        evidence=(
            "baixa confiança, oclusão, ambiguidade ou falha de componente",
            "nenhuma regra observável atingiu seu limiar",
        ),
        limitation="É o resultado seguro padrão e não deve ser convertido em avaliação negativa.",
    ),
)


@dataclass(frozen=True, slots=True)
class ActivityPolicy:
    """Auditable policy selected for one concrete work context."""

    policy_id: str
    version: int
    context: str
    thresholds: ActivityThresholds = field(default_factory=ActivityThresholds)
    states: tuple[ActivityStateDefinition, ...] = _OFFICE_COMPUTER_STATES

    def __post_init__(self) -> None:
        if not self.policy_id or self.policy_id != self.policy_id.strip():
            raise ValueError("policy_id deve ser preenchido e não conter espaços externos")
        if self.version < 1:
            raise ValueError("versão da política deve ser positiva")
        if not self.context.strip():
            raise ValueError("contexto da política deve ser preenchido")
        state_values = tuple(definition.state for definition in self.states)
        if len(set(state_values)) != len(state_values):
            raise ValueError("política não pode repetir estados")
        if set(state_values) != set(ActivityState):
            raise ValueError("política deve definir exatamente todos os estados observáveis")

    def definition_for(self, state: ActivityState) -> ActivityStateDefinition:
        """Return the definition for a state without silently accepting unknown values."""

        return next(definition for definition in self.states if definition.state is state)


DEFAULT_OFFICE_COMPUTER_POLICY = ActivityPolicy(
    policy_id="office-computer",
    version=1,
    context="Uma pessoa em uma estação fixa de trabalho com computador.",
)
