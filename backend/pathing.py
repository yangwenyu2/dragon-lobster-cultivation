from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'data'
FRONTEND_DIR = PROJECT_ROOT / 'frontend'
ASSETS_DIR = FRONTEND_DIR / 'assets'


def data_path(*parts: str) -> Path:
    return DATA_DIR.joinpath(*parts)
