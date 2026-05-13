from __future__ import annotations

import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    load_dotenv()
    api_id = int(os.environ["TELETHON_API_ID"])
    api_hash = os.environ["TELETHON_API_HASH"]
    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("Login selesai. Simpan value ini ke TELETHON_SESSION_STRING:")
        print(StringSession.save(client.session))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
