# Digest Hub

Multi-channel digest generator that fetches public sources, deduplicates items, scores and enriches them with LLMs, then sends HTML email digests through Gmail SMTP.

## Channels

| Channel | Path | Runtime | Schedule |
| --- | --- | --- | --- |
| Growth Radar | `channels/growth-radar` | Node.js | Daily 05:00 Beijing |
| Product Radar | `channels/product-radar` | Python | Daily 05:30 Beijing |
| Crypto | `channels/crypto` | Node.js | Daily 05:45 Beijing |
| Crypto Price | `channels/crypto-price` | Node.js | Daily 07:00 and 19:00 Beijing |
| AI Info | `channels/ai-info` | Node.js | Daily 07:30 Beijing |
| Investment | `channels/investment` | Python | Daily 07:30 Beijing |
| Growth Weekly | `channels/growth-weekly` | Node.js | Saturday 09:00 Beijing |
| Product Radar Weekly | `channels/product-radar/main_weekly.py` | Python | Saturday 10:00 Beijing |

## Required Secrets

GitHub Actions expects these repository secrets:

- `GMAIL_APP_PASSWORD`: Gmail 16-character app password. Required for email delivery.
- `DIGEST_RECIPIENT`: Email recipient. If omitted, code defaults to the sender address.
- `ZHIPU_API_KEY`: Key for the free `glm-4.7-flash` model. All AI calls are pinned to this model; paid-model environment variables are ignored.

## Local Runs

Node channels:

```bash
npm install
npm install --prefix channels/growth-radar
node channels/growth-radar/main.js --no-email
```

Python channels:

```bash
pip install -r channels/product-radar/requirements.txt
python channels/product-radar/main.py --no-email
```

Use `--no-score` for a fast dry run that skips LLM calls.

## Manual Dispatch

```bash
gh workflow run growth-radar.yml --repo yzeng1018/digest-hub
gh workflow run product-radar.yml --repo yzeng1018/digest-hub
gh workflow run crypto.yml --repo yzeng1018/digest-hub
gh workflow run morning-digest.yml --repo yzeng1018/digest-hub
```

Check recent runs:

```bash
gh run list --repo yzeng1018/digest-hub --limit 10
```

For local development, pass `--no-email` when you only want to generate output files.
