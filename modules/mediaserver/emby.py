from typing import Dict, List

import requests

from app.database.models.health import Health
from app.core.config import Settings
from app.utils import  timer_count
from app.utils.log import logger


class Emby:
    api_key: str
    server: str

    def __init__(self, settings: Settings):
        self.api_key = settings.EMBY_API_KEY
        self.server = settings.EMBY_URL.rstrip('/')

    def search(self, keyword) -> List[Dict]:
        if self.api_key and self.server:
            url = f"{self.server}/emby/Items"
            params = {
                'api_key': self.api_key,
                'SearchTerm': keyword,
                'IncludeItemTypes': 'Movie',
                'Recursive': 'true',
                'StartIndex': '0',
                'IncludeSearchTypes': 'false'
            }
            try:
                response = requests.get(url, params=params)
                if response.ok:
                    search_results = response.json()
                    return search_results['Items']
                else:
                    logger.error(f"EMBY查询出错: {response.status_code}")
            except Exception as e:
                logger.error(f"EMBY查询出错: {e}")
        return []

    @timer_count()
    def healthy_check(self):
        if self.api_key and self.server:
            url = f"{self.server}/emby/Items"
            params = {
                'api_key': self.api_key,
                'SearchTerm': "TEST",
                'IncludeItemTypes': 'Movie',
                'Recursive': 'false',
                'StartIndex': '0',
                'IncludeSearchTypes': 'false'
            }
            try:
                res = requests.get(url, params=params)
                if res.ok:
                    return Health({"module": "EMBY", "status": "healthy", "info": "success"})
                else:
                    return Health({"module": "EMBY", "status": "unhealthy", "info": f"状态码{res.status_code}"})
            except Exception as e:
                return Health({"module": "EMBY", "status": "unhealthy", "info": "网络异常"})
        else:
            return Health({"module": "EMBY", "status": "none", "info": "none"})
