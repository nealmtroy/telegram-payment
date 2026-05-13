from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _required(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Environment variable {name} wajib diisi.")
    return value.strip()


def _int(name: str, default: int | None = None) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        if default is None:
            raise RuntimeError(f"Environment variable {name} wajib diisi.")
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} harus angka.") from exc


def _bounded_int(
    name: str,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    value = _int(name, default)
    if minimum is not None and value < minimum:
        raise RuntimeError(f"Environment variable {name} minimal {minimum}.")
    if maximum is not None and value > maximum:
        raise RuntimeError(f"Environment variable {name} maksimal {maximum}.")
    return value


def _admin_ids() -> set[int]:
    raw = _required("ADMIN_IDS")
    ids: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            ids.add(int(item))
        except ValueError as exc:
            raise RuntimeError("ADMIN_IDS harus berisi angka dipisah koma.") from exc
    if not ids:
        raise RuntimeError("ADMIN_IDS minimal berisi 1 admin id.")
    return ids


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    telethon_api_id: int
    telethon_api_hash: str
    telethon_session_string: str
    vip_group_id: int | str
    saweria_username: str
    payment_amount: int
    payment_email: str
    payment_expire_minutes: int
    payment_check_interval_seconds: int
    vip_invite_expire_hours: int
    vip_invite_usage_limit: int
    db_path: str
    log_level: str


def load_settings() -> Settings:
    load_dotenv()
    vip_group_raw = _required("VIP_GROUP_ID")
    try:
        vip_group_id: int | str = int(vip_group_raw)
    except ValueError:
        vip_group_id = vip_group_raw

    return Settings(
        bot_token=_required("BOT_TOKEN"),
        admin_ids=_admin_ids(),
        telethon_api_id=_int("TELETHON_API_ID"),
        telethon_api_hash=_required("TELETHON_API_HASH"),
        telethon_session_string=_required("TELETHON_SESSION_STRING"),
        vip_group_id=vip_group_id,
        saweria_username=_required("SAWERIA_USERNAME"),
        payment_amount=_bounded_int("PAYMENT_AMOUNT", minimum=1000),
        payment_email=os.getenv("PAYMENT_EMAIL", "member@example.com").strip(),
        payment_expire_minutes=_bounded_int(
            "PAYMENT_EXPIRE_MINUTES",
            30,
            minimum=1,
            maximum=1440,
        ),
        payment_check_interval_seconds=_bounded_int(
            "PAYMENT_CHECK_INTERVAL_SECONDS",
            20,
            minimum=5,
            maximum=3600,
        ),
        vip_invite_expire_hours=_bounded_int(
            "VIP_INVITE_EXPIRE_HOURS",
            6,
            minimum=1,
            maximum=24,
        ),
        vip_invite_usage_limit=_bounded_int(
            "VIP_INVITE_USAGE_LIMIT",
            1,
            minimum=1,
            maximum=1,
        ),
        db_path=os.getenv("DB_PATH", "payments.db").strip() or "payments.db",
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )
