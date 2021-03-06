import logging
from typing import Mapping, Optional, TYPE_CHECKING, Union

import aiohttp

from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog

from ..errors import YouTubeApiError

if TYPE_CHECKING:
    from .. import Audio

log = logging.getLogger("red.cogs.Audio.api.YouTube")

SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"


class YouTubeWrapper:
    """Wrapper for the YouTube Data API."""

    def __init__(
        self, bot: Red, config: Config, session: aiohttp.ClientSession, cog: Union["Audio", Cog]
    ):
        self.bot = bot
        self.config = config
        self.session = session
        self.api_key: Optional[str] = None
        self._token: Mapping[str, str] = {}
        self.cog = cog

    def update_token(self, new_token: Mapping[str, str]):
        self._token = new_token

    async def _get_api_key(self) -> str:
        """Get the stored youtube token"""
        if not self._token:
            self._token = await self.bot.get_shared_api_tokens("youtube")
        self.api_key = self._token.get("api_key", "")
        return self.api_key if self.api_key is not None else ""

    async def get_call(self, query: str) -> Optional[str]:
        """Make a Get call to youtube data api"""
        params = {
            "q": query,
            "part": "id",
            "key": await self._get_api_key(),
            "maxResults": 1,
            "type": "video",
        }
        async with self.session.request("GET", SEARCH_ENDPOINT, params=params) as r:
            if r.status in [400, 404]:
                return None
            elif r.status in [403, 429]:
                if r.reason == "quotaExceeded":
                    raise YouTubeApiError("Your YouTube Data API quota has been reached.")
                return None
            else:
                search_response = await r.json()
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                return f"https://www.youtube.com/watch?v={search_result['id']['videoId']}"

        return None
