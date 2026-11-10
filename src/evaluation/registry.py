from pathlib import Path

import joblib

from src.evaluation.promotion import should_promote


def promote_if_approved(
    baseline_metrics,
    candidate_metrics,
    candidate_path,
    approved_path,
    minimum_recall=0.90,
):
    approved = should_promote(
        baseline_metrics,
        candidate_metrics,
        minimum_recall=minimum_recall,
    )

    if not approved:
        return False

    candidate_path = Path(candidate_path)
    approved_path = Path(approved_path)

    if not candidate_path.is_file():
        raise FileNotFoundError(
            f"Candidate model not found: {candidate_path}"
        )

    approved_path.parent.mkdir(parents=True, exist_ok=True)

    # Charger puis sauvegarder le candidat uniquement après validation.
    candidate_model = joblib.load(candidate_path)
    joblib.dump(candidate_model, approved_path)

    return True
