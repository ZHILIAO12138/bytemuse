import requests

from app.database.models import Health
from app.core.config import Settings
from app.utils import timer_count


class DockerHub:
    proxy: str

    def __init__(self, settings: Settings):
        self.proxy = settings.PROXY

    @timer_count()
    def healthy_check(self):
        try:
            url = "https://hub.docker.com/v2/repositories/envyafish/byte-muse/tags/"
            proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
            res = requests.get(url, proxies=proxies, timeout=10)
            if res.ok:
                return Health({"module": "DOCKERHUB", "status": "healthy", "info": "success"})
            else:
                return Health({"module": "DOCKERHUB", "status": "unhealthy", "info": f"状态码{res.status_code}"})
        except Exception as e:
            return Health({"module": "DOCKERHUB", "status": "unhealthy", "info": "网络异常"})
