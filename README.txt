# Smart Healthcare Project Management System (Flask + SQLite)

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract this folder.
3. Open PowerShell inside this folder.
4. Run:
   `py -m venv .venv`
   `.\.venv\Scripts\Activate.ps1`
   `py -m pip install -r requirements.txt`
   `py app.py`
5. Open http://127.0.0.1:5000 in your browser.

## Demo login
- Username: `chawais`
- Password: `pakistan`
- Override the demo credentials in PowerShell before starting the app:
  `$env:SPM_USERNAME="your-username"`
  `$env:SPM_PASSWORD="your-password"`
  `$env:FLASK_SECRET_KEY="a-long-random-secret"`

This login is for the local coursework demo only. It is not production-grade authentication and must not be used to protect real healthcare data.

The SQLite database (`spm.db`) is created automatically and stores project data persistently.

## Modules
Dashboard/project charter; requirements and simple WBS register; change requests (approval updates budget, duration, and scope); schedule/resources and progress; cost tracking and EVM indicators; defect tracking and quality checklist; risk scoring and PDPC-style responses; printable report.

## Important demo assumptions
- Sample data is fictional and for coursework only.
- Planned Value (PV) uses a demonstrative 65% of activity cost because no date-based baseline or reporting date is provided. For a formal EVM system, compute PV from a time-phased baseline.
- Schedule display calculates activity end week but does not calculate a full critical path automatically; dependency relationships are recorded for review.
- This is a local educational prototype, not a production healthcare system. Do not enter real patient data. Audit logs, encryption, and deployment hardening are not implemented.
