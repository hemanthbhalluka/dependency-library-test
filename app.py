
from io import BytesIO
from pathlib import Path

import requests
import yaml
from flask import Flask, jsonify, request
from PIL import Image, ImageOps
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

app = Flask(__name__)
app.config["SECRET_KEY"] = "training-only-change-me"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


# Dependency 1 and 2: requests + urllib3
def make_http_session():
    session = requests.Session()

    retry = Retry(
        total=2,
        backoff_factor=0.1,
        status_forcelist=[502, 503, 504]
    )

    session.mount(
        "https://",
        HTTPAdapter(max_retries=retry)
    )
    return session


@app.get("/")
def index():
    return jsonify({
        "project": "Dependency Vulnerability Lab",
        "routes": [
            "/health",
            "/config",
            "/fetch?url=https://example.com",
            "/thumbnail"
        ]
    })


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


# Dependency 3: PyYAML
@app.get("/config")
def config_preview():
    config_file = DATA_DIR / "config.yaml"

    if not config_file.exists():
        config_file.write_text(
            "app_name: Dependency Lab\n"
            "theme: dark\n"
            "max_items: 20\n",
            encoding="utf-8"
        )

    try:
        config = yaml.safe_load(
            config_file.read_text(encoding="utf-8")
        ) or {}

        return jsonify({
            "config": config,
            "loader": "safe_load"
        })

    except yaml.YAMLError:
        return jsonify({"error": "Invalid YAML"}), 400


# Dependency 1 and 2: requests + urllib3
@app.get("/fetch")
def fetch():
    url = request.args.get(
        "url", "https://example.com"
    )

    # Basic guard for this local training example
    if not url.startswith("https://"):
        return jsonify({
            "error": "Only HTTPS URLs are allowed"
        }), 400

    try:
        response = make_http_session().get(
            url,
            timeout=4,
            allow_redirects=False
        )

        return jsonify({
            "requested_url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get(
                "content-type", ""
            ),
            "body_preview": response.text[:160]
        })

    except requests.RequestException:
        return jsonify({"error": "Fetch failed"}), 502


# Dependency 4: Pillow
@app.post("/thumbnail")
def thumbnail():
    uploaded = request.files.get("image")

    if not uploaded:
        return jsonify({
            "error": "Upload an image using field 'image'"
        }), 400

    try:
        image = Image.open(BytesIO(uploaded.read()))
        image = ImageOps.exif_transpose(image).convert("RGB")

        image.thumbnail((320, 320), Image.Resampling.LANCZOS)

        output = BytesIO()
        image.save(output, format="PNG")

        return jsonify({
            "width": image.width,
            "height": image.height,
            "png_bytes": len(output.getvalue()),
            "message": "Thumbnail generated"
        })

    except Exception:
        return jsonify({
            "error": "Unsupported or invalid image"
        }), 400


if __name__ == "__main__":
    # Local-only training server
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
