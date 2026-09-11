# Phishing Awareness Quiz

Interactive security-awareness quiz with **14 realistic, scenario-based questions**
covering modern phishing trends: QR phishing (quishing), MFA fatigue/push-bombing,
OAuth consent scams, fake tech support, AI-generated spear phishing, business email
compromise (BEC), malicious macro attachments, shortened-URL smishing, typosquatting,
bank smishing, DocuSign/file-share lures — plus legitimate control scenarios so
players must judge carefully instead of guessing "phishing" every time.

Each answer returns a detailed explanation, red flags, and the safe habit to build.

## Run locally

```bash
pip install -r phishing-quiz/requirements.txt
python -m flask --app phishing-quiz/api/app.py run --port 5000
# open http://127.0.0.1:5000
```

## Deploy (Vercel)

The app is a Flask project deployed as a Vercel serverless function
(`phishing-quiz/api/index.py`). The Vercel project root directory is `phishing-quiz/`.

```bash
cd phishing-quiz
vercel deploy --prod
```

## API

- `GET /` — quiz page
- `POST /check` — body `{"answers": {"1": "Phishing", ...}}` →
  `{"score": n, "total": 14, "feedback": [...]}`
- `GET /health` — `{"status": "ok", "questions": 14}`
