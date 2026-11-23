"""
Pawer Favorites & Pinned Workspaces — Persists and manages 1-click shortcuts to
favorite Streamlit scripts and local development URLs.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional


import tempfile


def _get_favorites_file() -> Path:
    """Returns path to the user's favorites.json storage file with safe fallbacks."""
    # 1. Prefer project workspace directory
    try:
        project_dir = Path(__file__).resolve().parent.parent.parent / ".pawer"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir / "favorites.json"
    except Exception:
        pass

    # 2. Try OS temp directory
    try:
        tmp_dir = Path(tempfile.gettempdir()) / "Pawer"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir / "favorites.json"
    except Exception:
        pass

    # 3. Fallback to APPDATA
    appdata = os.getenv("APPDATA")
    fav_dir = Path(appdata) / "Pawer" if appdata else Path.home() / ".pawer"
    fav_dir.mkdir(parents=True, exist_ok=True)
    return fav_dir / "favorites.json"


def load_favorites() -> List[Dict]:
    """Loads all pinned workspace favorites."""
    path = _get_favorites_file()
    if not path.exists():
        # Default starter favorites
        defaults = [
            {
                "id": "fav_sample",
                "name": "Sample Streamlit Dashboard",
                "target": "examples/sample_streamlit_app.py",
                "icon": "🎈",
                "type": "streamlit",
            },
            {
                "id": "fav_fastapi",
                "name": "FastAPI Docs (Swagger)",
                "target": "http://localhost:8000/docs",
                "icon": "⚡",
                "type": "url",
            },
        ]
        save_favorites(defaults)
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_favorites(favorites: List[Dict]) -> bool:
    """Saves the list of favorites to disk."""
    path = _get_favorites_file()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(favorites, f, indent=2)
        return True
    except Exception:
        return False


def add_favorite(name: str, target: str, icon: str = "⭐") -> Dict:
    """Adds a new pinned project workspace or URL."""
    favs = load_favorites()
    fav_id = f"fav_{uuid.uuid4().hex[:8]}"
    fav_type = "streamlit" if target.endswith(".py") else "url"
    new_fav = {
        "id": fav_id,
        "name": name.strip(),
        "target": target.strip(),
        "icon": icon,
        "type": fav_type,
    }
    favs.append(new_fav)
    save_favorites(favs)
    return new_fav


def remove_favorite(fav_id: str) -> bool:
    """Removes a pinned favorite by ID."""
    favs = load_favorites()
    filtered = [f for f in favs if f.get("id") != fav_id]
    if len(filtered) != len(favs):
        save_favorites(filtered)
        return True
    return False
