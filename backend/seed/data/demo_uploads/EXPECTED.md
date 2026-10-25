# Expected demo uploads

- `demo_clean.csv`: 20 accepted, 0 flagged, 0 rejected; every row has no issues.
- `demo_messy.csv`: 15 accepted, 0 flagged, 15 rejected; rows 2-16 have no issues and rows 17-31 have `DUP_IN_FILE`.
- `demo_overflow.csv`: 60 accepted, 5 flagged, 0 rejected; rows 2-61 have no issues and rows 62-66 have `INTAKE_EXCEEDED`.
