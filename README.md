# Northstar

Northstar is a free, self-service job alert platform for friends and early-career candidates. A polished GitHub Pages site collects role, location, graduation year, and email preferences. A Cloudflare Worker verifies consent, stores private subscriber data in D1, matches new StateJobsNY vacancies, and delivers alerts through Resend. The existing Python scanner runs on GitHub Actions.

## How it works

```text
Friend -> GitHub Pages -> Worker -> D1 + confirmation email

GitHub Actions -> StateJobsNY -> Python scanner -> private Worker endpoint
                                                    |
                                            match + deduplicate
                                                    |
                                              Resend alert
```

Subscriber emails and API credentials never enter the public repository or GitHub Pages. Subscriptions use double opt-in, and every alert has a unique unsubscribe link.

## Project structure

- `web/` — static Northstar website deployed to GitHub Pages
- `worker/` — Cloudflare Worker API and D1 schema
- `app/job_alert/` — StateJobsNY scanner and normalized job ingestion
- `.github/workflows/pages.yml` — website deployment
- `.github/workflows/job-alert.yml` — scheduled vacancy monitor

## Deploy the website

The Pages workflow deploys `web/` on every push to `main`. On GitHub, open **Settings → Pages → Build and deployment**, choose **GitHub Actions**, then run **Deploy Northstar website** under Actions. The default URL is `https://abhiishekk02.github.io/StateJobsNY-Alerts/`.

## Deploy the API

Requirements: a free Cloudflare account, a free Resend account, and a domain verified in Resend.

```bash
cd worker
npm install
npx wrangler login
npx wrangler d1 create northstar-alerts
```

Copy the returned database ID into `worker/wrangler.toml`, then initialize and configure it:

```bash
npm run db:remote
npx wrangler secret put RESEND_API_KEY
npx wrangler secret put INGEST_API_KEY
npm run deploy
```

Use a long random value for `INGEST_API_KEY`. Set `FROM_EMAIL` in `wrangler.toml` to a sender on your verified Resend domain. Then put the deployed `workers.dev` URL in `web/config.js` and push that change.

## Connect GitHub Actions

Add these repository secrets under **Settings → Secrets and variables → Actions**:

- `ALERT_API_URL` — deployed Worker origin, without a trailing slash
- `ALERT_API_KEY` — the same random value stored as `INGEST_API_KEY`

The older Gmail SMTP secrets remain supported as a fallback but are not required when the API variables are configured. Run **NY State Job Alert** manually once to verify the connection.

## Local development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt -e .
pytest
ruff check .
```

For the website, run `python -m http.server 8080 --directory web`. For the Worker, run `npm install`, `npm run db:local`, and `npm run dev` inside `worker/`.

## Privacy and operating notes

- The service stores name, email, graduation year, preferences, consent timestamp, and delivery history.
- Avoid logging request bodies or email addresses.
- Cloudflare D1 is the source of truth for subscriptions; never commit subscriber exports.
- The project is independent and is not affiliated with New York State.

## License

[MIT](LICENSE)
