"""
PC Express (Maxi) OAuth2 authentication.

Flow:
1. User runs `python -m src.main auth --store maxi`
2. Playwright opens headed browser to maxi.ca login
3. User logs in manually (handles CAPTCHA if needed)
4. We capture the redirect URI with auth code
5. Exchange auth code for refresh token
6. Store encrypted refresh token

Subsequent runs: refresh token → access token automatically.
"""

import asyncio
import logging
from urllib.parse import parse_qs, urlparse

import aiohttp

from src.auth.token_store import get_token, set_token
from src.config import PCEXPRESS_API_BASE, PCEXPRESS_API_KEY

logger = logging.getLogger(__name__)

# PC ID OAuth2 endpoints (Loblaw)
TOKEN_ENDPOINT = "https://api.pcexpress.ca/pcid/v1/oauth2/token"
AUTH_URL = (
    "https://www.maxi.ca/login?returnUrl=%2F"
)

# Static client ID baked into PC Express web app
CLIENT_ID = "0oa3q3m7tJi5LKYD02p7"
REDIRECT_URI = "https://www.maxi.ca/auth/callback"


async def exchange_code_for_tokens(auth_code: str) -> dict:
    """Troca authorization code por access token + refresh token."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            TOKEN_ENDPOINT,
            json={
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
            },
            headers={
                "Content-Type": "application/json",
                "x-apikey": PCEXPRESS_API_KEY,
                "Business-User-Agent": "PCXWEB",
            },
        ) as resp:
            data = await resp.json()
            logger.info("Token exchange response: %s", resp.status)
            if resp.status != 200:
                raise RuntimeError(f"Token exchange failed: {data}")
            return data


async def refresh_access_token(refresh_token: str) -> dict:
    """Usa refresh token para obter novo access token."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            TOKEN_ENDPOINT,
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": CLIENT_ID,
            },
            headers={
                "Content-Type": "application/json",
                "x-apikey": PCEXPRESS_API_KEY,
                "Business-User-Agent": "PCXWEB",
            },
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"Refresh failed: {data}")
            # Store new refresh token (rotation)
            if "refresh_token" in data:
                set_token("maxi", data["refresh_token"])
            return data


async def get_access_token() -> str:
    """Retorna um access token valido para PC Express API."""
    refresh_token = get_token("maxi")
    if not refresh_token:
        raise RuntimeError(
            "Maxi nao autenticado. Rode: python -m src.main auth --store maxi"
        )
    tokens = await refresh_access_token(refresh_token)
    return tokens["access_token"]


async def capture_auth_code_from_browser() -> str:
    """
    Abre o navegador para login manual no Maxi.
    Captura o auth code do redirect URI.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        auth_code_future: asyncio.Future[str] = asyncio.get_running_loop().create_future()

        async def handle_response(response):
            if REDIRECT_URI in response.url and "code=" in response.url:
                parsed = urlparse(response.url)
                params = parse_qs(parsed.query)
                code = params.get("code", [None])[0]
                if code and not auth_code_future.done():
                    auth_code_future.set_result(code)

        page.on("response", handle_response)

        await page.goto(AUTH_URL)
        print("\n=== Faca login no Maxi no navegador ===")
        print("Aguardando autenticacao...\n")

        try:
            code = await auth_code_future
            print("Auth code capturado!")
        except Exception:
            print("Timeout ou falha na autenticacao.")
            raise
        finally:
            await browser.close()

        return code


async def login_maxi_interactive() -> None:
    """Fluxo completo de login interativo para Maxi."""
    code = await capture_auth_code_from_browser()
    tokens = await exchange_code_for_tokens(code)
    if "refresh_token" in tokens:
        set_token("maxi", tokens["refresh_token"])
        print("Maxi autenticado com sucesso! Token salvo.")
    else:
        raise RuntimeError(f"Resposta inesperada: {tokens}")
