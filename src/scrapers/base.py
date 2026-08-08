import asyncio
import logging
import time
from abc import ABC, abstractmethod

from src.config import MAX_RETRIES, TIMEOUT_SECONDS
from src.models import Price, ScrapeResult

logger = logging.getLogger(__name__)


class AbstractScraper(ABC):
    store_id: str
    store_name: str

    @abstractmethod
    async def search_product(self, product_slug: str, search_terms: list[str]) -> list[Price]:
        """Search for a product and return list of prices found."""

    async def scrape(self, product_slug: str, search_terms: list[str]) -> list[Price]:
        start = time.monotonic()
        last_error: str | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await asyncio.wait_for(
                    self.search_product(product_slug, search_terms),
                    timeout=TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                last_error = f"timeout ({TIMEOUT_SECONDS}s)"
                logger.warning("%s: timeout attempt %d/%d", self.store_id, attempt, MAX_RETRIES)
            except Exception as e:
                last_error = str(e)
                logger.error("%s: attempt %d/%d error: %s", self.store_id, attempt, MAX_RETRIES, e)
                await asyncio.sleep(2 ** attempt)

        elapsed = (time.monotonic() - start) * 1000
        logger.error("%s: all retries failed: %s", self.store_id, last_error)
        return []  # Return empty on failure, don't raise (partial results)

    async def run(self, product_slug: str, search_terms: list[str]) -> ScrapeResult:
        start = time.monotonic()
        try:
            prices = await self.scrape(product_slug, search_terms)
            elapsed = (time.monotonic() - start) * 1000
            return ScrapeResult(
                store_id=self.store_id,
                store_name=self.store_name,
                prices=prices,
                duration_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return ScrapeResult.empty(
                store_id=self.store_id,
                store_name=self.store_name,
                error=str(e),
            )
