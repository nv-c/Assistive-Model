# Running the Drishti project (local development)

This document describes step-by-step instructions to run the frontend (Expo web) and backend (Flask + ML workers) locally on macOS.

## Quick summary
- Backend API: http://127.0.0.1:5001
- Expo Web (frontend): http://localhost:19006

## Prerequisites (macOS)
- Homebrew (recommended)
- Python 3 (3.9+), Node.js, npm/yarn
- System packages: `tesseract`, `ffmpeg`

Install common system deps:

```bash
brew update
brew install python@3.9 tesseract ffmpeg
# (optional) install a stable Node LTS if you need one
# brew install node@18
```

## Backend setup (Python virtualenv)
1. Create & activate virtualenv (if not already present):

```bash
cd /Users/chirag/new/Drishti-See-the-World-with-us
python3 -m venv backend/.venv
source backend/.venv/bin/activate
```

2. Upgrade pip and install Python requirements:

```bash
pip install -U pip setuptools wheel
# Prefer the curated requirements file if present
pip install -r backend/requirements_final.txt || pip install -r backend/requirements.txt
```

Notes:
- If installs fail, inspect the error and consider installing binary deps (e.g., OpenCV, libtiff) via Homebrew.

## Frontend (Expo web) setup
1. From project root, install JS deps (if not already installed):

```bash
npm install
# or `yarn` if you prefer
```

2. Start the Expo web dev server:

```bash
# If you see the Node/OpenSSL error (ERR_OSSL_EVP_UNSUPPORTED), run with the legacy provider:
NODE_OPTIONS=--openssl-legacy-provider npm run web
# otherwise:
npm run web
```

After successful build the web UI is available at `http://localhost:19006` (also on your LAN IP).

## Running the backend server
With the venv activated run:

```bash
source backend/.venv/bin/activate
PYTHONUNBUFFERED=1 backend/.venv/bin/python backend/app.py
```

The Flask dev server will start on port `5001` (0.0.0.0 / 127.0.0.1). The front-end reads the backend host dynamically from `window.location.hostname` (see `constants/constants.js`).

## Useful endpoints & quick tests
- OCR (document):

```bash
curl -F "file=@backend/final/images/photo.jpg" http://127.0.0.1:5001/text-doc -i
```

- OCR (non-document):

```bash
curl -F "file=@backend/final/images/photo.jpg" http://127.0.0.1:5001/text-non-doc -i
```

- Currency prediction (example — upload a short video/webm):

```bash
curl -F "file=@/path/to/video.webm" http://127.0.0.1:5001/currency -i
```

- Send location (JSON):

```bash
curl -X POST -H "Content-Type: application/json" -d '{"emailList":["you@example.com"]}' http://127.0.0.1:5001/send-location
```

## OCR manual test (isolated subprocess)
To run the heavy OCR pipeline manually (helps reproduce/diagnose OOM issues):

```bash
cd backend
# Recommended: limit native threads to reduce memory pressure
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  .venv/bin/python -m final.OCR final/images doc
```

## Environment variables
- Optional SMTP for `/send-location`: set `DRISHTI_SMTP_USER` and `DRISHTI_SMTP_PASS` in your shell to enable real email sending.
- Optional SMS gateway: `DRISHTI_SMS_GATEWAY` if your environment uses SMS notifications.

Example:

```bash
export DRISHTI_SMTP_USER=you@example.com
export DRISHTI_SMTP_PASS=yourpassword
export DRISHTI_SMS_GATEWAY=https://sms.example/send
```

## Troubleshooting
- Node/OpenSSL build error (openssl/crypto error): run Expo with:

```bash
NODE_OPTIONS=--openssl-legacy-provider npm run web
```

- If OCR subprocess is killed (exit code 137 / "Killed: 9") it is likely an OOM. Mitigations:
  - Run the OCR subprocess with limited threads (see OCR manual test above).
  - Ensure `tesseract` and `ffmpeg` are installed via Homebrew.
  - Run on a machine with more RAM, or run the OCR/currency models on a dedicated inference host.

- If tesseract binary is not found, install it:

```bash
brew install tesseract
```

- If ffmpeg is missing (used for webm/transcode), install it:

```bash
brew install ffmpeg
```

## Key code locations
- Backend API: [backend/app.py](backend/app.py)
- Currency worker: [backend/currency_predict.py](backend/currency_predict.py)
- OCR pipeline: [backend/final/OCR.py](backend/final/OCR.py)
- Page dewarp (controls remap sizes): [backend/final/page_dewarp/page_dewarp.py](backend/final/page_dewarp/page_dewarp.py)
- Frontend constants (backend host): [constants/constants.js](constants/constants.js)

## Next steps / suggestions
- Remove or silence debug prints once you confirm behavior in the wild.
- Consider running heavy ML models in a persistent worker process (or separate service) to avoid repeated imports and reduce OOM risk.

---
