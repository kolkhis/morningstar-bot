import os
import aiohttp

# Uses email delivery to send a Tremendous reward to a recipient. The reward is created using the Tremendous API.

REQUEST_TIMEOUT_SECONDS = 15


class TremendousClient:
    def __init__(self):
        self.api_key = os.environ["TREMENDOUS_API_KEY"]
        self.base_url = os.environ.get(
            "TREMENDOUS_BASE_URL",
            "https://testflight.tremendous.com/api/v2",
        )

    async def create_email_reward(
        self,
        *,
        recipient_name: str,
        recipient_email: str,
        amount_usd: float,
        product_ids: list[str],
    ) -> dict:
        url = f"{self.base_url}/orders"

        payload = {
            "payment": {
                "funding_source_id": "BALANCE",
            },
            "reward": {
                "value": {
                    "denomination": amount_usd,
                    "currency_code": "USD",
                },
                "delivery": {
                    "method": "EMAIL",
                },
                "recipient": {
                    "name": recipient_name,
                    "email": recipient_email,
                },
                "products": product_ids,
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    data = await resp.json(content_type=None)

                    if resp.status >= 400:
                        raise RuntimeError(
                            f"Tremendous API error {resp.status}: {data}"
                        )

                    return data
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to reach Tremendous API: {e}") from e
