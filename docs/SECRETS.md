# GitHub secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.

## Subscriber delivery (recommended)

- `ALERT_API_URL`: deployed Cloudflare Worker origin.
- `ALERT_API_KEY`: same random value saved in Cloudflare as `INGEST_API_KEY`.

When both are present, SMTP is not used.

## Direct Gmail fallback

- `EMAIL_ADDRESS`: Gmail address used to send alerts.
- `EMAIL_PASSWORD`: a Google App Password, not the normal account password. Enable 2-Step Verification and create an App Password in the Google Account security settings.

SMTP connection values:

- `SMTP_SERVER`: `smtp.gmail.com`
- `SMTP_PORT`: `587`

Never commit credentials to YAML, `.env`, logs, issues, or screenshots. GitHub masks registered secrets in action output.
