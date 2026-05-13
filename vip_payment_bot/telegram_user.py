from __future__ import annotations

from datetime import datetime, timedelta, timezone

from telethon import TelegramClient, functions
from telethon.sessions import StringSession

from .config import Settings


class TelegramUserClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = TelegramClient(
            StringSession(settings.telethon_session_string),
            settings.telethon_api_id,
            settings.telethon_api_hash,
        )

    async def start(self) -> None:
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError("TELETHON_SESSION_STRING tidak valid atau belum login.")

    async def close(self) -> None:
        await self.client.disconnect()

    async def create_vip_invite_link(self, order_id: int) -> str:
        expire_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.vip_invite_expire_hours
        )
        result = await self.client(
            functions.messages.ExportChatInviteRequest(
                peer=self.settings.vip_group_id,
                expire_date=expire_at,
                usage_limit=self.settings.vip_invite_usage_limit,
                title=f"VIP payment #{order_id}",
            )
        )
        link = getattr(result, "link", None)
        if not link:
            raise RuntimeError("Telethon tidak mengembalikan invite link.")
        return str(link)
