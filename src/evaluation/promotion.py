def should_promote(baseline_metrics, candidate_metrics, minimum_recall=0.90):
    recall_ok = (
        candidate_metrics["recall_malignant"] >= minimum_recall
    )
    f1_ok = (
        candidate_metrics["f1_malignant"]
        >= baseline_metrics["f1_malignant"]
    )

    return recall_ok and f1_ok
