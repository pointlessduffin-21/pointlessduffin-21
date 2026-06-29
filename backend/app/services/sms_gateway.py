import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_sms(
    destination: str,
    content: str,
    port: int = 1,
    gateway_url: str | None = None,
    gateway_account: str | None = None,
    gateway_password: str | None = None,
) -> dict:
    """
    Sends an SMS via the T200 gateway.
    Optional overrides for gateway URL, account, password (from DB settings).
    Returns dict with keys: success (bool), raw_response (str), credits_used (int)
    """
    url = gateway_url or settings.SMS_GATEWAY_URL
    account = gateway_account or settings.SMS_GATEWAY_ACCOUNT
    password = gateway_password or settings.SMS_GATEWAY_PASSWORD

    params = {
        "1500101": (
            f"account={account}"
            f"&password={password}"
            f"&port={port}"
            f"&destination={destination}"
            f"&content={content}"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.text

        # Parse the T200 response — typical format is CGI success/failure codes
        # Common patterns: success contains "OK" or specific codes
        success = "OK" in raw.upper() or "SUCCESS" in raw.upper() or "SEND" in raw.upper()

        # Estimate credits (1 credit per 160 chars by default, adjust as needed)
        credits = max(1, (len(content) + 159) // 160)

        return {
            "success": success,
            "raw_response": raw[:1000],
            "credits_used": credits,
        }
    except httpx.HTTPError as e:
        logger.error(f"SMS gateway HTTP error: {e}")
        return {
            "success": False,
            "raw_response": str(e)[:1000],
            "credits_used": 0,
        }
    except Exception as e:
        logger.error(f"SMS gateway error: {e}")
        return {
            "success": False,
            "raw_response": str(e)[:1000],
            "credits_used": 0,
        }
