from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PaymentRequest:
    transaction_id: str | None
    payment_url: str | None
    qr_path: str | None
    raw: Any


class SaweriaPayments:
    def __init__(self, username: str, email: str) -> None:
        self.username = username
        self.email = email

    async def create_payment(self, amount: int, message: str) -> PaymentRequest:
        return await asyncio.to_thread(self._create_payment_sync, amount, message)

    async def is_paid(self, transaction_id: str) -> bool:
        return await asyncio.to_thread(self._is_paid_sync, transaction_id)

    def _create_payment_sync(self, amount: int, message: str) -> PaymentRequest:
        from qris_saweria import create_payment_qr

        self._validate_saweria_profile()
        safe_message = "".join(
            character if character.isalnum() else "-"
            for character in message.lower()
        ).strip("-")
        target = Path(tempfile.gettempdir()) / f"qris-{safe_message or 'payment'}.png"
        try:
            qr_string, transaction_id, qr_path = create_payment_qr(
                self.username,
                amount,
                self.email,
                output_path=str(target),
                use_template=False,
            )
        except Exception as exc:
            if "Saweria account not found" in str(exc):
                raise RuntimeError(
                    f"Akun Saweria '{self.username}' tidak ditemukan dari server. "
                    "Pastikan SAWERIA_USERNAME isi username saja. Jika username sudah benar, "
                    "kemungkinan Saweria memberi response berbeda ke IP hosting."
                ) from exc
            raise
        return PaymentRequest(
            transaction_id=transaction_id,
            payment_url=None,
            qr_path=qr_path,
            raw={"qr_string": qr_string, "transaction_id": transaction_id},
        )

    def _is_paid_sync(self, transaction_id: str) -> bool:
        from qris_saweria import check_paid_status

        return bool(check_paid_status(transaction_id))

    def _validate_saweria_profile(self) -> None:
        import json
        import re
        import requests

        url = f"https://saweria.co/{self.username}"
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(
                f"Saweria profile '{self.username}' gagal dibuka: HTTP {response.status_code}."
            )

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
            re.DOTALL,
        )
        if not match:
            raise RuntimeError(
                f"Saweria profile '{self.username}' tidak mengandung __NEXT_DATA__. "
                "Kemungkinan response Saweria dari IP hosting berbeda atau diblok."
            )

        data = json.loads(match.group(1))
        profile = data.get("props", {}).get("pageProps", {}).get("data", {})
        if not profile.get("id"):
            raise RuntimeError(
                f"Saweria profile '{self.username}' terbuka, tapi user id tidak ditemukan."
            )
