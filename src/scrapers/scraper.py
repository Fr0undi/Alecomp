from typing import Optional

import httpx
import logging

logger = logging.getLogger(__name__)


class PageScraper:

    async def scrape_page(self, url: str) -> Optional[str]:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as Client:
            try:
                response = await Client.get(url)
                return response.text
            except Exception as e:
                logger.error(f"Ошибка при получении html: {e}")
                return None