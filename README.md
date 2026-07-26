# Digest Hub

Multi-channel digest generator that fetches public sources, deduplicates items, scores and enriches them with LLMs, then sends HTML email digests through Gmail SMTP.

## Channels

| Channel | Path | Runtime | Schedule |
| --- | --- | --- | --- |
| Product Radar | `channels/product-radar` | Python | Daily 05:30 Beijing |
| Crypto | `channels/crypto` | Node.js | Daily 05:45 Beijing; includes a CoinGecko market snapshot |
| AI Info | `channels/ai-info` | Node.js | Daily 07:30 Beijing |
| Investment | `channels/investment` | Python | Daily 07:30 Beijing |
| Growth Weekly | `channels/growth-weekly` | Node.js | Saturday 09:00 Beijing |
| Product Radar Weekly | `channels/product-radar/main_weekly.py` | Python | Saturday 10:00 Beijing |

## Required Secrets

GitHub Actions expects these repository secrets:

- `GMAIL_APP_PASSWORD`: Gmail 16-character app password. Required for email delivery.
- `DIGEST_RECIPIENT`: Email recipient. If omitted, code defaults to the sender address.
- `DEEPSEEK_API_KEY`: DeepSeek API key for `deepseek-v4-flash`.
- `QWEN_API_KEY`: Alibaba Cloud Model Studio key for `qwen-max`.

## Model A/B Experiment

DeepSeek V4 Flash and Qwen Max rotate daily using the Beijing calendar. The four
daily emails are balanced 2:2, and every channel switches model the next day.
The model printed in each email is the model that actually produced the result.

Optional controls:

- `MODEL_AB_OVERRIDE=deepseek` or `MODEL_AB_OVERRIDE=qwen` forces one arm.
- `MODEL_AB_DATE=2026-07-27` reproduces the assignment for a specific date.
- `DEEPSEEK_MODEL`, `QWEN_MODEL`, and `QWEN_BASE_URL` override provider settings.

## Local Runs

Node channels:

```bash
npm install
npm install --prefix channels/crypto
node channels/crypto/main.js --no-email --no-score
```

Python channels:

```bash
pip install -r channels/product-radar/requirements.txt
python channels/product-radar/main.py --no-email
```

Use `--no-score` for a fast dry run that skips LLM calls.

## Manual Dispatch

```bash
gh workflow run product-radar.yml --repo yzeng1018/digest-hub
gh workflow run crypto.yml --repo yzeng1018/digest-hub
gh workflow run morning-digest.yml --repo yzeng1018/digest-hub
```

Check recent runs:

```bash
gh run list --repo yzeng1018/digest-hub --limit 10
```

For local development, pass `--no-email` when you only want to generate output files.
