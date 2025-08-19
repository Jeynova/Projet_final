import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

from core.spec_extractor import SpecExtractor

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
    # Compatible with both Pydantic v1 and v2
    spec_dict = spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict()
    return render_template("preview.html", spec=spec_dict, conf=conf, prompt=prompt)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)