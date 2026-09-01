import os
from dataclasses import dataclass


@dataclass
class Config:
    listen_addr: str
    data_dir: str
    auth_enabled: bool
    auth_password: str
    log_level: str
    dev_mode: bool


def load_config() -> Config:
    cfg = Config(
        listen_addr=os.getenv("LISTEN_ADDR", "127.0.0.1:8080"),
        data_dir=os.getenv("DATA_DIR", "./data"),
        auth_enabled=_get_bool("AUTH_ENABLED", False),
        auth_password=os.getenv("AUTH_PASSWORD", ""),
        log_level=os.getenv("LOG_LEVEL", "info"),
        dev_mode=_get_bool("DEV_MODE", False),
    )
    if cfg.auth_enabled and not cfg.auth_password:
        raise ValueError("AUTH_PASSWORD is required when AUTH_ENABLED=true")
    valid_levels = {"debug", "info", "warn", "error"}
    if cfg.log_level not in valid_levels:
        raise ValueError(f"Invalid LOG_LEVEL: {cfg.log_level!r}, must be one of {valid_levels}")
    return cfg


def _get_bool(key: str, default: bool) -> bool:
    val = os.getenv(key, "")
    if not val:
        return default
    return val.lower() in ("true", "1", "yes")
