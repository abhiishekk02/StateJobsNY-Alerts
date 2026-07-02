# NY State Job Alert

A production-oriented Python service that checks [StateJobsNY](https://statejobs.ny.gov/public/search.cfm) every 15 minutes and emails newly posted vacancies matching all configured title, location, and grade rules. GitHub Actions runs it in the cloud, so no personal computer needs to remain online.

## Features

- Uses the official vacancy search with server-side grade and region constraints.
- Applies exact configured rules locally after normalizing each vacancy detail page.
- Retries transient HTTP failures with exponential backoff and reuses one HTTP session.
- Sends auto-escaped HTML plus plain-text fallback through Gmail SMTP with STARTTLS.
- Atomically records a vacancy only after SMTP accepts its alert.
- Persists IDs in Git through a concurrency-safe scheduled workflow.
- Emits readable console logs and rotating local logs; workflow logs are retained as artifacts.
- Fails clearly when configuration, remote markup, state, network, or SMTP is invalid.

## Architecture

```text
GitHub scheduler
  -> StateJobsClient -> search result parser -> cheap title filter
  -> detail parser -> location + grade filter -> EmailNotifier
  -> atomic SeenJobStore -> Git commit/push
```

`app/job_alert/` separates HTTP, parsing, filtering, notifications, state, configuration, logging, and orchestration. Search parameters narrow the source request to Grade 18 in Capital/Saratoga; the application verifies Albany and every other required rule from normalized posting fields.

## Project tree

```text
.
├── .github/workflows/job-alert.yml
├── app/job_alert/
│   ├── cli.py                 # process entry point and error boundary
│   ├── client.py              # resilient HTTP session
│   ├── config.py              # typed YAML/env configuration
│   ├── filters.py             # all-required matching
│   ├── parser.py              # result/detail normalization
│   ├── notifier.py            # HTML rendering and Gmail SMTP
│   ├── service.py             # application orchestration
│   └── storage.py             # atomic duplicate state
├── config/config.yaml
├── data/seen_jobs.json
├── docs/SECRETS.md
├── templates/job_alert.html
├── tests/
├── requirements.txt
└── pyproject.toml
```

## Local setup

Requirements: Python 3.12+ and a Gmail account with 2-Step Verification and an App Password.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt -e .
export EMAIL_ADDRESS='sender@gmail.com'
export EMAIL_PASSWORD='your-16-character-app-password'
export SMTP_SERVER='smtp.gmail.com'
export SMTP_PORT='587'
python -m job_alert --config config/config.yaml
```

The recipient is already configured as `abhishek@gmail.com`. Override it without editing YAML with `EMAIL_RECIPIENT`. Never put passwords in the repository. Run tests with:

```bash
pytest --cov=job_alert
ruff check .
```

## GitHub deployment

1. Create a GitHub repository and push this project to its default branch.
2. Add the four Actions secrets in [the secrets guide](docs/SECRETS.md): `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `SMTP_SERVER`, and `SMTP_PORT`.
3. Open **Actions → NY State Job Alert → Run workflow** for the first verification run.
4. Confirm the run can write repository contents. The workflow declares `contents: write`; if organization policy overrides it, enable **Settings → Actions → General → Workflow permissions → Read and write permissions**.
5. Leave Actions enabled. UTC cron runs every 15 minutes; GitHub may delay scheduled jobs during high load.

The workflow serializes runs, checks out the default branch, runs the monitor, uploads logs even on failure, and commits `data/seen_jobs.json` only when an email was accepted. A failed SMTP attempt is not marked seen and is retried later.

## Configuration

All non-secret settings live in [`config/config.yaml`](config/config.yaml). Change keywords, locations, grades, StateJobsNY URLs, region IDs, recipient, SMTP defaults, retry policy, timeouts, user agent, paths, and logging there. [`config/config.example.yaml`](config/config.example.yaml) is a compact starting point.

When adding multiple grades, note that the current source request uses the first grade to minimize downloads, while the matcher accepts every configured grade. For monitoring several grades simultaneously, prefer separate workflows/config files so each source query remains selective.

## Expected workflow

1. Request Grade 18 vacancies in Capital/Saratoga.
2. Parse unique vacancy IDs and titles.
3. Skip IDs already emailed and titles without any configured keyword.
4. Download only candidate details and require Albany plus Grade 18.
5. Send one professional HTML alert per new match.
6. Atomically save the ID and commit updated state.

## Example email

> **🚨 New NY State Job Match Found**  
> **Python Developer**  
> Agency: Office of Information Technology Services  
> Grade: 18 · Salary: $65,001–$82,656  
> Employment type: Full-Time · Location: Albany  
> Posted: 07/02/2026 · Deadline: 07/17/2026  
> **View job posting**  
> Alert generated 2026-07-02 14:15:00 UTC

To add real screenshots after the first run, redact email addresses and secrets, save images under `docs/images/`, and embed them here with `![Alert email](docs/images/alert-email.png)`.

## Example logs

```text
2026-07-02T14:15:01+0000 INFO job_alert.cli - NY State job alert run started
2026-07-02T14:15:02+0000 INFO job_alert.service - Search returned 14 vacancy records
2026-07-02T14:15:03+0000 INFO job_alert.service - Alert sent for vacancy 123456: Python Developer
2026-07-02T14:15:03+0000 INFO job_alert.cli - Run complete: found=14 matched=1 sent=1 already_seen=2 duration=2.31s
```

## Troubleshooting

- **Authentication failed:** use a Google App Password, not the normal Gmail password. Confirm 2-Step Verification is enabled.
- **Missing configuration:** verify all four GitHub secrets and exact secret names. Secrets are case-sensitive.
- **Parser says markup changed:** inspect the uploaded log artifact and StateJobsNY page before updating parser fixtures. The application exits nonzero rather than silently claiming success.
- **Push rejected:** enable read/write workflow permissions. Concurrency prevents this workflow from racing itself; another process editing state may still require a rerun.
- **No alerts:** the vacancy must match a title keyword, Albany, and Grade 18. Review the search count in logs and run manually.
- **Schedule appears late:** GitHub schedules are best-effort and can queue during busy periods; manual dispatch remains available.

## Verification checklist

- [ ] Tests and lint pass on Python 3.12.
- [ ] Gmail App Password is stored only as a GitHub secret.
- [ ] Manual workflow run finishes successfully.
- [ ] Logs artifact contains start, counts, duration, and useful errors.
- [ ] A known matching fixture renders escaped HTML correctly.
- [ ] `data/seen_jobs.json` changes only after successful email delivery.
- [ ] A second run skips the persisted vacancy ID.
- [ ] Scheduled workflow has repository write permission.

## Contributing

Create a focused branch, add tests for behavior changes, run `pytest` and `ruff check .`, then open a pull request explaining any StateJobsNY markup assumptions. Do not include live credentials or personally identifying log output.

## License

[MIT](LICENSE)
