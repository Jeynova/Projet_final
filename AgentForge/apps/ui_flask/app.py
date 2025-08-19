import os, subprocess, json
from pathlib import Path
from flask import Flask, render_template, request, send_file, redirect, url_for
from dotenv import load_dotenv
import sys

# Add the project root to the path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

# NEW imports - now using absolute imports
try:
    from apps.ui_flask.db import Base, engine, SessionLocal
    from apps.ui_flask.models import Project, DockerImage
except ImportError:
    # Fallback for when running directly
    from db import Base, engine, SessionLocal
    from models import Project, DockerImage

# Load environment variables
load_dotenv()

from core.spec_extractor import SpecExtractor
from orchestrator.graph import build_app as build_graph

app = Flask(__name__)
extractor = SpecExtractor()

GENERATED = ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

# NEW: init DB
Base.metadata.create_all(bind=engine)

def zip_project(project_dir: Path) -> Path:
    """Create a zip archive of the project directory"""
    zip_path = project_dir.parent / f"{project_dir.name}.zip"
    import shutil
    base_name = str(zip_path.with_suffix(""))
    shutil.make_archive(base_name, "zip", project_dir)
    return zip_path

@app.get("/")
def index():
    # NEW: liste des derniers projets
    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.desc()).limit(10).all()
    finally:
        db.close()
    return render_template("index.html", projects=projects)

@app.post("/preview")
def preview():
    prompt = request.form.get("prompt", "").strip()
    name = request.form.get("name", "").strip() or "generated-project"
    if not prompt:
        # Get projects for error page
        db = SessionLocal()
        try:
            projects = db.query(Project).order_by(Project.id.desc()).limit(10).all()
        finally:
            db.close()
        return render_template("index.html", error="Merci de saisir un prompt.", projects=projects)
    
    spec, conf = extractor.extract(prompt)
    # Compatible with both Pydantic v1 and v2
    spec_dict = spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict()
    return render_template("preview.html", spec=spec_dict, conf=conf, prompt=prompt, name=name)

@app.post("/generate")
def generate():
    """Generate a complete project from prompt"""
    prompt = request.form.get("prompt", "").strip()
    name = request.form.get("name", "").strip() or "generated-app"
    if not prompt:
        return redirect(url_for("index"))

    app_graph = build_graph()
    state = {"prompt": prompt, "name": name, "artifacts_dir": str(GENERATED), "logs": []}
    final = app_graph.invoke(state)
    
    project_dir = Path(final["project_dir"])
    zip_path = zip_project(project_dir)

    # NEW: persist project in database
    db = SessionLocal()
    try:
        p = Project(
            name=name,
            prompt=prompt,
            status=final.get("status", "unknown"),
            project_path=str(project_dir),
            zip_path=str(zip_path),
            logs_path=str(GENERATED / f"{name}_logs.json"),  # Assuming logs are saved here
        )
        db.add(p)
        db.commit()
        project_id = p.id
    finally:
        db.close()

    logs = final.get("logs", [])
    status = final.get("status", "unknown")
    return render_template(
        "result.html",
        prompt=prompt,
        name=name,
        logs=logs,
        status=status,
        download_url=url_for("download_zip", filename=zip_path.name),
        project_path=str(project_dir),
        project_id=project_id,
    )

@app.get("/download/<path:filename>")
def download_zip(filename):
    """Download generated project zip file"""
    f = GENERATED / filename
    return send_file(f, as_attachment=True)

# NEW: build & push image vers un registre (Docker Hub / GHCR)
@app.post("/push-image/<int:project_id>")
def push_image(project_id: int):
    """Build and push Docker image for a project"""
    registry = os.getenv("DOCKER_REGISTRY", "docker.io")  # ex ghcr.io
    image_ns = os.getenv("DOCKER_NAMESPACE", "youruser")  # org/user
    image_tag = os.getenv("DOCKER_TAG", "latest")

    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return "Projet introuvable", 404

        proj_dir = Path(proj.project_path)
        image_name = f"{image_ns}/{proj.name}:{image_tag}"

        try:
            # build
            subprocess.check_call(["docker", "build", "-t", image_name, "."], cwd=proj_dir)
            # login si nécessaire (tu peux utiliser DOCKER_USERNAME/DOCKER_TOKEN en .env)
            user = os.getenv("DOCKER_USERNAME")
            token = os.getenv("DOCKER_TOKEN")
            if user and token:
                subprocess.check_call(["docker", "login", "-u", user, "--password-stdin", registry], input=token.encode())

            # push
            subprocess.check_call(["docker", "push", image_name])

            di = DockerImage(
                project_id=project_id,
                image_name=image_name.split(":")[0],
                image_tag=image_tag,
                registry_url=f"{registry}/{image_ns}/{proj.name}",
                pushed=True,
                push_log="OK",
            )
            db.add(di)
            db.commit()
        except subprocess.CalledProcessError as e:
            di = DockerImage(
                project_id=project_id,
                image_name=image_name.split(":")[0] if ":" in image_name else image_name,
                image_tag=image_tag,
                registry_url=f"{registry}/{image_ns}/{proj.name}",
                pushed=False,
                push_log=str(e),
            )
            db.add(di)
            db.commit()
            return f"Push échoué: {e}", 500
    finally:
        db.close()

    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)