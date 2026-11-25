# Neythal (நெய்தல்)
Coastal intelligence prototype for the BUILD 2036 Climate & Clean Energy hackathon.
Neythal is the Sangam-era Tamil word for the seashore landscape. Pilot: Gulf of Mannar.

## Run (Windows)
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    streamlit run app.py
    python tests\test_models.py

## Honest limits
Prototype decision-support tool. Scores are screening aids, not validated predictions.
Demo mode uses synthetic data and is always labelled. Species records are not abundance.
Habitat and pollution feeds are not connected yet. Never harvest seagrass for energy.

## Security notes
HTTPS-only allow-listed hosts, timeouts, response-size cap, numeric-only query values,
escaped text in HTML, input validation in models, XSRF on, localhost bind, no secrets in repo.
Run `pip install pip-audit && pip-audit` before submission.
