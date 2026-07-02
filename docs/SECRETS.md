# GitHub secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret**.

Required:

- `EMAIL_ADDRESS`: Gmail address used to send alerts.
- `EMAIL_PASSWORD`: a Google App Password, not the normal account password. Enable 2-Step Verification and create an App Password in the Google Account security settings.

Recommended (the workflow expects these so they are explicit):

- `SMTP_SERVER`: `smtp.gmail.com`
- `SMTP_PORT`: `587`

Never commit credentials to YAML, `.env`, logs, issues, or screenshots. GitHub masks registered secrets in action output.

