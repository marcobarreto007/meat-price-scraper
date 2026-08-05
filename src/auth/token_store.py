import json
import logging
from pathlib import Path

from cryptography.fernet import Fernet

from src.config import CACHE_DIR

logger = logging.getLogger(__name__)

TOKEN_FILE = CACHE_DIR / "tokens.enc"
KEY_FILE = CACHE_DIR / ".fernet_key"


def _get_fernet() -> Fernet:
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
    else:
        key = Fernet.generate_key()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        KEY_FILE.write_bytes(key)
    return Fernet(key)


def save_tokens(tokens: dict) -> None:
    f = _get_fernet()
    data = f.encrypt(json.dumps(tokens).encode())
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_bytes(data)
    logger.info("Tokens saved to %s", TOKEN_FILE)


def load_tokens() -> dict:
    if not TOKEN_FILE.exists():
        return {}
    try:
        f = _get_fernet()
        data = f.decrypt(TOKEN_FILE.read_bytes())
        return json.loads(data.decode())
    except Exception:
        logger.warning("Failed to decrypt token store, starting fresh")
        return {}


def get_token(store: str) -> str | None:
    tokens = load_tokens()
    return tokens.get(store)


def set_token(store: str, token: str) -> None:
    tokens = load_tokens()
    tokens[store] = token
    save_tokens(tokens)
