import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from pathlib import Path

from core.spec_extractor import SpecExtractor

load_dotenv()
app = Flask(__name__)
extractor = SpecExtractor()

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/preview")
def preview():
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return render_template("index.html", error="Merci de saisir un prompt.")
    spec, conf = extractor.extract(prompt)
    return render_template("preview.html", spec=spec.model_dump(), conf=conf, prompt=prompt)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)