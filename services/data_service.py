# Não esquecer de executar o venv\Services\activate
# para poder testar o código rodando no terminal


from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict


DEFAULT_DATA: Dict[str, Any] = {
    "version": 1,
    "habits": [],
    "entries": [],
}


@dataclass(frozen=True)
class DataPaths:
    data_file: Path

def get_default_paths() -> DataPaths:
    # services/ -> project root -> data/habits.json
    project_root = Path(__file__).resolve().parents[1]
    return DataPaths(data_file=project_root / "data" / "habits.json")


def ensure_data_dir_exists(paths: DataPaths) -> None:
    paths.data_file.parent.mkdir(parents=True, exist_ok=True)


def validate_data_shape(data: Any) -> Dict[str, Any]:
    """
    Minimal shape validation to prevent runtime errors.
    Keeps it flexible for future migrations.
    """
    if not isinstance(data, dict):
        raise ValueError("Data file root must be a JSON object.")

    version = data.get("version", 1)
    habits = data.get("habits", [])
    entries = data.get("entries", [])

    if not isinstance(version, int):
        raise ValueError("'version' must be an integer.")
    if not isinstance(habits, list):
        raise ValueError("'habits' must be a list.")
    if not isinstance(entries, list):
        raise ValueError("'entries' must be a list.")

    # Normalize: ensure keys exist
    data["version"] = version
    data["habits"] = habits
    data["entries"] = entries
    return data


def load_data(paths: DataPaths | None = None) -> Dict[str, Any]:
    paths = paths or get_default_paths()
    ensure_data_dir_exists(paths)

    if not paths.data_file.exists():
        save_data(DEFAULT_DATA, paths)
        return DEFAULT_DATA.copy()

    try:
        raw = paths.data_file.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        return validate_data_shape(parsed)
    except (json.JSONDecodeError, OSError, ValueError):
        # Fallback: keep a backup of the corrupted file
        backup_name = f"habits.corrupted.{date.today().isoformat()}.json"
        backup_path = paths.data_file.parent / backup_name
        try:
            backup_path.write_text(paths.data_file.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass

        save_data(DEFAULT_DATA, paths)
        return DEFAULT_DATA.copy()


def save_data(data: Dict[str, Any], paths: DataPaths | None = None) -> None:
    paths = paths or get_default_paths()
    ensure_data_dir_exists(paths)

    validated = validate_data_shape(data)
    payload = json.dumps(validated, ensure_ascii=False, indent=2)
    paths.data_file.write_text(payload + "\n", encoding="utf-8")
