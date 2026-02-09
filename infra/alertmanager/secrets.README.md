Alertmanager secrets

For security, place secrets (not checked into git) under `infra/alertmanager/secrets/` which is mounted into the Alertmanager container at `/etc/alertmanager/secrets/`.

Supported secret files (create these files with appropriate values):
- `slack_api_url` — full Slack incoming webhook URL
- `smtp_smarthost` — SMTP host:port (e.g., smtp.example.com:587)
- `smtp_username` — SMTP username
- `smtp_identity` — SMTP identity (often same as username)
- `telegram_webhook` — Telegram bot webhook URL

Example (Linux):
  mkdir -p infra/alertmanager/secrets
  echo "https://hooks.slack.com/services/TOKEN" > infra/alertmanager/secrets/slack_api_url
  chmod 600 infra/alertmanager/secrets/*

Do NOT commit secrets to git. Use a vault or CI secret management for production deployments and mount them at runtime.
