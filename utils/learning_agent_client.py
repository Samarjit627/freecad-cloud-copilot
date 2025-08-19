import os
import json
from typing import Optional, Dict, Any

# Prefer requests if available; otherwise fall back to urllib
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None

import urllib.request
import urllib.error
import mimetypes
import uuid

CONFIG_PATH = os.path.expanduser("/Users/samarjit/CascadeProjects/freecad-cloud-copilot/cloud_config.json")


def _load_cloud_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    # Expected keys (new learning agent block)
    la = cfg.get("learning_agent", {})
    base_url = la.get("base_url") or cfg.get("base_url") or cfg.get("service_url")
    api_key = la.get("api_key") or cfg.get("api_key") or os.getenv("LEARNING_AGENT_API_KEY") or os.getenv("X_API_KEY")

    # Provide sane defaults; caller should validate
    return {
        "base_url": (base_url or "").rstrip("/"),
        "api_key": api_key or "",
        "ingest_path": la.get("ingest_path", "/api/ingest"),
        "timeout": la.get("timeout", 120),
    }


def _guess_mime(path: str) -> str:
    mt, _ = mimetypes.guess_type(path)
    return mt or "application/octet-stream"


def _post_multipart_urllib(url: str, fields: Dict[str, str], file_field: str, file_path: str, headers: Dict[str, str], timeout: int = 120) -> str:
    boundary = uuid.uuid4().hex
    boundary_bytes = boundary.encode()
    data_parts = []

    for name, value in fields.items():
        data_parts.extend([
            b"--" + boundary_bytes + b"\r\n",
            f'Content-Disposition: form-data; name="{name}"'.encode(),
            b"\r\n\r\n",
            value.encode("utf-8"),
            b"\r\n",
        ])

    filename = os.path.basename(file_path)
    mime = _guess_mime(file_path)
    with open(file_path, "rb") as f:
        file_content = f.read()

    data_parts.extend([
        b"--" + boundary_bytes + b"\r\n",
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode(),
        b"\r\n",
        f"Content-Type: {mime}".encode(),
        b"\r\n\r\n",
        file_content,
        b"\r\n",
        b"--" + boundary_bytes + b"--\r\n",
    ])

    body = b"".join(data_parts)

    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def upload_cad(file_path: str, category: str, tags: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """Upload a CAD file to the Learning Agent.

    Args:
        file_path: Absolute path to the CAD file (STEP/IGES/FCStd/STL/OBJ)
        category: e.g. "wheel", "disc_brake", "chassis"
        tags: optional comma-separated tags string
        notes: optional notes string

    Returns:
        dict with {success: bool, status_code: int, response: str/json}
    """
    cfg = _load_cloud_config()
    base_url = cfg.get("base_url", "")
    api_key = cfg.get("api_key", "")
    ingest_path = cfg.get("ingest_path", "/api/ingest")
    timeout = int(cfg.get("timeout", 120))

    if not base_url:
        return {"success": False, "status_code": 0, "response": "Missing learning agent base_url in cloud_config.json (learning_agent.base_url)"}
    if not os.path.isfile(file_path):
        return {"success": False, "status_code": 0, "response": f"File not found: {file_path}"}

    url = f"{base_url.rstrip('/')}{ingest_path}"

    fields = {
        "category": category,
        "tags": tags or "",
        "notes": notes or "",
    }

    headers = {
        "X-API-Key": api_key,
    }

    # Try requests first for nicer errors
    if requests is not None:
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, _guess_mime(file_path))}
                resp = requests.post(url, headers=headers, data=fields, files=files, timeout=timeout)
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            return {"success": resp.ok, "status_code": resp.status_code, "response": payload}
        except Exception as e:  # fall through to urllib
            last_err = str(e)
    else:
        last_err = None

    # Fallback: urllib multipart
    try:
        text = _post_multipart_urllib(url, fields, "file", file_path, headers, timeout=timeout)
        return {"success": True, "status_code": 200, "response": text}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"success": False, "status_code": e.code, "response": body}
    except Exception as e:
        msg = f"Upload failed. requests_error={last_err} urllib_error={e}"
        return {"success": False, "status_code": 0, "response": msg}


def parse_category_from_text(text: str) -> Optional[str]:
    t = (text or "").lower()
    # simple heuristics; macro can override
    if "wheel" in t:
        return "wheel"
    if "disc" in t and ("brake" in t or "discbrake" in t or "disk" in t):
        return "disc_brake"
    if "chassis" in t:
        return "chassis"
    return None
