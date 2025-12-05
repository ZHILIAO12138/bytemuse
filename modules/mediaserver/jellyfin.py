from typing import Dict, List

import requests

from app.database.models.health import Health
from app.core.config import Settings
from app.utils import timer_count
from app.utils.log import logger


class Jellyfin:
    server: str = ''
    api_key: str = ''
    user: str = ''

    def __init__(self, settings: Settings):
        self.server = settings.JELLYFIN_URL.rstrip('/')
        self.api_key = settings.JELLYFIN_API_KEY
        self.user = settings.JELLYFIN_USER

    def search(self, keyword) -> List[Dict]:
        if self.server and self.api_key and self.user:
            url = f"{self.server}/Items"
            params = {
                'api_key': self.api_key,
                'searchTerm': keyword,
                'IncludeItemTypes': 'Movie',
                'Recursive': 'true'
            }
            try:
                response = requests.get(url, params=params)
                if response.ok:
                    search_results = response.json()
                    return search_results['Items']
                else:
                    logger.error(f"Jellyfin搜索出错: {response.status_code}")
            except Exception as e:
                logger.error(f"Jellyfin搜索出错: {e}")
        return []

    @timer_count()
    def healthy_check(self):
        if self.server and self.api_key and self.user:
            url = f"{self.server}/Items"
            params = {
                'api_key': self.api_key,
                'searchTerm': 'TEST',
                'IncludeItemTypes': 'Movie',
                'Recursive': 'false'
            }
            try:
                res = requests.get(url, params=params)
                if res.ok:
                    return Health({"module": "JELLYFIN", "status": "healthy", "info": "success"})
                else:
                    return Health({"module": "JELLYFIN", "status": "unhealthy", "info": f"状态码{res.status_code}"})
            except Exception as e:
                return Health({"module": "JELLYFIN", "status": "unhealthy", "info": "网络异常"})
        else:
            return Health({"module": "JELLYFIN", "status": "none", "info": "none"})
