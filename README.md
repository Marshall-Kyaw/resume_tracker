# Job Application Tracker

A local web app (Streamlit + SQLite) for tracking job applications: pipeline
status, resume versions, follow-ups, and interview rounds — with a dashboard.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

This opens the app at `http://localhost:8501`. Data is stored in a local
`job_tracker.db` SQLite file in the same folder — nothing leaves your
machine.

## Pages

- **Dashboard** — total/active/interviewing/offer counts, response rate,
  status breakdown, applications by market, applications-over-time trend,
  and a "stale applications" flag (active applications untouched for 14+
  days).
- **Applications** — full table with filters (status, market, text search),
  CSV export, and inline edit/delete.
- **Add Application** — form to log a new application. Fields: company,
  role, target market, status, date applied, resume version, source,
  job URL, referral contact, salary range, notes.
- **Follow-ups** — schedule follow-up actions per application; overdue ones
  are flagged in red.
- **Interviews** — log interview rounds per application (type, date,
  outcome, notes) and see full history.

## Customizing

- `db.STATUS_OPTIONS`, `db.MARKET_OPTIONS`, `db.SOURCE_OPTIONS` in `db.py`
  control the dropdown choices — edit these lists to match your pipeline
  (e.g. add more markets or statuses).
- The database schema is created automatically on first run
  (`db.init_db()`), so no manual setup is needed.

## Extending further

Ideas if you want to keep building on this:
- Email/Telegram reminders for follow-ups (e.g. via a scheduled script
  hitting `db.get_follow_ups()`)
- A browser extension or bookmarklet that POSTs a job URL into the app
- Resume-version-to-response-rate analysis once you have more data
- Deploying it (e.g. Streamlit Community Cloud) if you want access from
  your phone — note this would put your data on a third-party server,
  so keep that in mind if the notes field contains sensitive details.
