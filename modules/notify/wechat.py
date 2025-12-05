import requests
import json

from app.database.models.health import Health
from app.core.config import Settings
from app.utils import timer_count
from app.utils.log import logger


class WeChatNotifier:
    corp_id: str
    corp_secret: str
    agent_id: str
    api_host: str
    wechat_photo: str
    wechat_banner: bool
    user_ids: str

    def __init__(self, settings: Settings):
        self.corp_id = settings.WECHAT_CORP_ID
        self.corp_secret = settings.WECHAT_CORP_SECRET
        self.agent_id = settings.WECHAT_AGENT_ID
        self.api_host = settings.WECHAT_PROXY if settings.WECHAT_PROXY else 'https://qyapi.weixin.qq.com'
        self.wechat_photo = settings.WECHAT_PHOTO
        self.wechat_banner = settings.WECHAT_BANNER
        self.user_ids = settings.WECHAT_TO_USER

    def get_access_token(self):
        if self.corp_id and self.corp_secret and self.agent_id:
            url = f"{self.api_host}/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
            try:
                response = requests.get(url)
                response_data = response.json()
                if response_data['errcode'] == 0:
                    return response_data['access_token']
                else:
                    logger.error(f"获取微信token失败: {response_data['errmsg']}")
            except Exception as e:
                logger.error(f"获取微信token失败: {e}")

    def send_text_message(self, content):
        if self.corp_id and self.corp_secret and self.agent_id:
            access_token = self.get_access_token()
            url = f"{self.api_host}/cgi-bin/message/send?access_token={access_token}"
            payload = {
                "touser": self.user_ids,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content
                }
            }
            try:
                response = requests.post(url, data=json.dumps(payload))
                response_data = response.json()
                if response_data['errcode'] != 0:
                    logger.error(f"发送微信消息失败: {response_data['errmsg']}")
            except Exception as e:
                logger.error(f"发送微信消息失败: {e}")

    def send_photo_message(self, title, content, banner=''):
        if self.corp_id and self.corp_secret and self.agent_id:
            access_token = self.get_access_token()
            url = f"{self.api_host}/cgi-bin/message/send?access_token={access_token}"
            payload = {
                "touser": self.user_ids,
                "msgtype": "news",
                "agentid": self.agent_id,
                "news": {
                    "articles": [
                        {
                            "title": title,
                            "description": content,
                            "url": "",
                            "picurl": banner if self.wechat_banner else self.wechat_photo
                        }
                    ]
                }
            }
            try:
                response = requests.post(url, data=json.dumps(payload))
                response_data = response.json()
                if response_data['errcode'] != 0:
                    logger.error(f"发送微信消息失败: {response_data['errmsg']}")
            except Exception as e:
                logger.error(f"发送微信消息失败: {e}")

    @timer_count()
    def healthy_check(self):
        if self.corp_id and self.corp_secret and self.agent_id:
            url = f"{self.api_host}/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
            try:
                response = requests.get(url)
                if response.ok:
                    response_data = response.json()
                    if response_data['errcode'] == 0:
                        return Health({"module": "WECHAT", "status": "healthy", "info": "success"})
                    else:
                        return Health({"module": "WECHAT", "status": "unhealthy", "info": response_data['errmsg']})
                return Health({"module": "WECHAT", "status": "unhealthy", "info": f"状态码{response.status_code}"})
            except Exception as e:
                return Health({"module": "WECHAT", "status": "unhealthy", "info": "网络异常"})
        else:
            return Health({"module": "WECHAT", "status": "none", "info": "none"})
