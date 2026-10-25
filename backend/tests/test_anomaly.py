from app.services.anomaly import detect_cross_dup_clusters, detect_institution_anomalies, quality_score, risk_score

def student(**extra):
    row={"programme_code":"P", "admission_type":"REGULAR", "nri":"N", "oci":"N", "fn":"N", "admission_date":"2026-08-14", "status":"ACCEPTED"}; row.update(extra); return row

def test_supernumerary_and_foreign_thresholds():
    assert not detect_institution_anomalies([student(admission_type="SUPERNUMERARY")]+[student() for _ in range(9)], [], 0, [])
    alerts=detect_institution_anomalies([student(admission_type="SUPERNUMERARY") for _ in range(2)]+[student() for _ in range(8)], [], 0, [])
    assert alerts[0].rule_code=="ANOM_SUPERNUMERARY_SHARE" and "2 of 10" in alerts[0].message
    assert not any(a.rule_code=="ANOM_FOREIGN_SHARE" for a in detect_institution_anomalies([student(nri="Y")]+[student() for _ in range(9)], [], .05, []))
    assert any(a.rule_code=="ANOM_FOREIGN_SHARE" for a in detect_institution_anomalies([student(nri="Y") for _ in range(2)]+[student() for _ in range(8)], [], .05, []))

def test_date_reject_and_clusters_deterministic():
    assert not any(a.rule_code=="ANOM_DATE_BURST" for a in detect_institution_anomalies([student(admission_date="a") for _ in range(19)], [], 0, []))
    alerts=detect_institution_anomalies([student() for _ in range(20)]+[student(admission_date="b") for _ in range(20)], [], 0, [{"total_rows":10,"rejected":4}])
    assert {a.rule_code for a in alerts} >= {"ANOM_DATE_BURST","ANOM_REJECT_RATE"}
    assert not detect_cross_dup_clusters([{"institution_ids":[1,2]}]*2)
    assert detect_cross_dup_clusters([{"institution_ids":[2,1]}]*3)[0].evidence["duplicates"]==3
    assert alerts == detect_institution_anomalies([student() for _ in range(20)]+[student(admission_date="b") for _ in range(20)], [], 0, [{"total_rows":10,"rejected":4}])

def test_scores():
    assert quality_score(0,0,0)==100 and quality_score(8,2,10)==90
    assert risk_score(1,2,3,80)==75 and risk_score(4,5,6,0)==100
