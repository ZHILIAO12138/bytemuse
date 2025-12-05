from typing import Dict, List

from plexapi.server import PlexServer

from app.database.models.health import Health
from app.core.config import Settings
from app.utils import logger, timer_count


class Plex:
    server: PlexServer = None
    plex_url: str = None
    plex_token: str = None

    def __init__(self, settings: Settings):
        self.plex_url = settings.PLEX_URL
        self.plex_token = settings.PLEX_TOKEN
        if self.plex_url and self.plex_token:
            try:
                self.server = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
            except Exception as e:
                logger.error(f"Plex连接失败: {e}")

    def search(self, keyword) -> List[Dict]:
        if self.server:
            try:
                return self.server.search(keyword)
            except Exception as e:
                logger.error(f"Plex连接失败: {e}")
        return []

    @timer_count()
    def healthy_check(self):
        if self.plex_url and self.plex_token:
            try:
                self.server = PlexServer(self.plex_url, self.plex_token)
                return Health({"module": "PLEX", "status": "healthy", "info": "success"})
            except Exception as e:
                return Health({"module": "PLEX", "status": "unhealthy", "info": "fail"})
        else:
            return Health({"module": "PLEX", "status": "none", "info": "none"})
