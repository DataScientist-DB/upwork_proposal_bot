from __future__ import annotations

from app.config import DECISION_THRESHOLDS
from app.models import DecisionType, GateResult, ScoreBreakdown


def get_confidence_label(confidence: int) -> str:
    if confidence >= 75:
        return "HIGH"
    if confidence >= 50:
        return "MEDIUM"
    return "LOW"


def decide(gate: GateResult, scores: ScoreBreakdown) -> DecisionType:
    if not gate.passed:
        if scores.final_score >= 75:
            return "CONDITIONAL_APPLY"
        return "SKIP"

    # Extreme blockers only
    extreme_risk = (
        scores.client_quality < 20
        or scores.clarity < 15
        or scores.execution_risk >= 85
    )
    if extreme_risk:
        return "SKIP"

    # ------------------------------------------------------------
    # Strong score band
    # Can downgrade to APPLY, but should not jump to SKIP here
    # ------------------------------------------------------------
    if scores.final_score >= DECISION_THRESHOLDS["strong_apply"]:
        severe_downgrade = (
            scores.competition_risk >= 80
            or scores.execution_risk >= 75
            or (scores.clarity < 30 and scores.client_quality < 35)
        )

        moderate_downgrade = (
            scores.competition_risk >= 70
            or scores.client_quality < 45
            or scores.execution_risk >= 65
            or (scores.clarity < 40 and scores.execution_risk >= 55)
        )

        if severe_downgrade:
            return "APPLY"

        if moderate_downgrade:
            return "APPLY"

        return "STRONG_APPLY"

    # ------------------------------------------------------------
    # Apply score band
    # Can downgrade to CONDITIONAL_APPLY, but should not become
    # STRONG_APPLY just because risk is low
    # ------------------------------------------------------------
    if scores.final_score >= DECISION_THRESHOLDS["apply"]:
        high_risk = (
            scores.competition_risk >= 75
            or scores.client_quality < 35
            or scores.execution_risk >= 75
            or (scores.clarity < 30 and scores.client_quality < 45)
        )

        medium_risk = (
            scores.competition_risk >= 65
            or scores.client_quality < 45
            or scores.execution_risk >= 65
            or (scores.clarity < 40 and scores.execution_risk >= 55)
        )

        if high_risk:
            return "CONDITIONAL_APPLY"

        if medium_risk:
            return "APPLY"

        return "APPLY"

    # ------------------------------------------------------------
    # Conditional band
    # Can stay CONDITIONAL_APPLY or upgrade to APPLY
    # ------------------------------------------------------------
    if scores.final_score >= DECISION_THRESHOLDS["conditional"]:
        high_risk = (
            scores.competition_risk >= 65
            or scores.client_quality < 45
            or scores.execution_risk >= 65
            or (scores.clarity < 40 and scores.client_quality < 60)
        )

        medium_risk = (
            scores.competition_risk >= 55
            or scores.client_quality < 50
            or (scores.clarity < 40 and scores.execution_risk >= 50)
        )

        if high_risk:
            return "CONDITIONAL_APPLY"

        if medium_risk and scores.final_score < DECISION_THRESHOLDS["apply"] - 5:
            return "CONDITIONAL_APPLY"

        # only promote to APPLY when the conditional-band case looks clean
        is_clean_opportunity = bool(
            scores.client_quality >= 50
            and scores.clarity >= 40
            and scores.execution_risk < 50
            and scores.competition_risk < 55
        )

        if is_clean_opportunity:
            return "APPLY"

        return "CONDITIONAL_APPLY"

    return "SKIP"