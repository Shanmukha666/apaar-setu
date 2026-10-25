"""Pure, explainable rule-based anomaly detection. Owner: P2."""
from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class AnomalyAlert:
    rule_code: str
    severity: str
    message: str
    evidence: dict
    programme_code: str | None = None


def _percent(part: int, total: int) -> int:
    return round(100 * part / total) if total else 0


def detect_institution_anomalies(students: list[dict], programmes: list[dict], peer_foreign_share_median: float, upload_stats: list[dict]) -> list[AnomalyAlert]:
    enrolled = [student for student in students if student.get("status") != "REJECTED"]
    alerts: list[AnomalyAlert] = []
    by_programme: dict[str, list[dict]] = defaultdict(list)
    for student in enrolled: by_programme[student.get("programme_code", "")].append(student)
    for code, items in by_programme.items():
        supernumerary = sum(item.get("admission_type") == "SUPERNUMERARY" for item in items)
        if len(items) >= 10 and supernumerary / len(items) > .10:
            alerts.append(AnomalyAlert("ANOM_SUPERNUMERARY_SHARE", "WARNING", f"{_percent(supernumerary, len(items))}% of enrolment ({supernumerary} of {len(items)}) in programme {code} is supernumerary; threshold is 10%.", {"supernumerary": supernumerary, "enrolment": len(items), "threshold_pct": 10}, code))
    foreign = sum(any(item.get(flag) == "Y" for flag in ("nri", "oci", "fn")) for item in enrolled)
    threshold = max(.15, 2 * peer_foreign_share_median)
    if enrolled and foreign / len(enrolled) > threshold:
        alerts.append(AnomalyAlert("ANOM_FOREIGN_SHARE", "WARNING", f"{_percent(foreign, len(enrolled))}% of enrolment ({foreign} of {len(enrolled)}) has NRI, OCI, or FN status; threshold is {round(threshold * 100)}%.", {"foreign": foreign, "enrolment": len(enrolled), "threshold_pct": threshold * 100}, None))
    dates = Counter(item.get("admission_date") for item in enrolled)
    if dates:
        admission_date, amount = sorted(dates.items(), key=lambda pair: (-pair[1], pair[0]))[0]
        if amount >= 20 and amount / len(enrolled) >= .40:
            alerts.append(AnomalyAlert("ANOM_DATE_BURST", "WARNING", f"{_percent(amount, len(enrolled))}% of admissions ({amount} of {len(enrolled)}) share admission date {admission_date}; threshold is 40%.", {"admission_date": admission_date, "count": amount, "enrolment": len(enrolled), "threshold_pct": 40}, None))
    for index, upload in enumerate(upload_stats, start=1):
        total, rejected = upload.get("total_rows", 0), upload.get("rejected", 0)
        if total and rejected / total > .30:
            alerts.append(AnomalyAlert("ANOM_REJECT_RATE", "INFO", f"Upload {index} rejected {_percent(rejected, total)}% of rows ({rejected} of {total}); threshold is 30%.", {"upload_index": index, "rejected": rejected, "total_rows": total, "threshold_pct": 30}, None))
    return sorted(alerts, key=lambda alert: (alert.rule_code, alert.programme_code or ""))


def detect_cross_dup_clusters(duplicates: list[dict]) -> list[AnomalyAlert]:
    pairs = Counter(tuple(sorted(item["institution_ids"])) for item in duplicates)
    alerts = [AnomalyAlert("ANOM_CROSS_DUP_CLUSTER", "WARNING", f"{count} cross-institution duplicates involve institutions {pair[0]} and {pair[1]}; threshold is 3.", {"institution_ids": list(pair), "duplicates": count, "threshold": 3}, None) for pair, count in pairs.items() if count >= 3]
    return sorted(alerts, key=lambda alert: (alert.rule_code, alert.programme_code or "", alert.evidence["institution_ids"]))


def quality_score(accepted: int, flagged: int, total_rows: int) -> int:
    return 100 if total_rows == 0 else round(100 * (accepted + .5 * flagged) / total_rows)


def risk_score(programmes_over_intake: int, anomaly_alerts: int, cross_dups: int, quality: int) -> int:
    return min(100, 30 * programmes_over_intake + 10 * anomaly_alerts + 5 * cross_dups + (100 - quality) // 2)
