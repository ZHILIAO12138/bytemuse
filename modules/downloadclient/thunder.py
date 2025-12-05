import re

import requests

from app.core.config import Settings, get_settings
from app.utils import logger


class Thunder:
    url: str = None
    file_id: str = None
    device_id: str = None
    authorization: str = None

    def __init__(self, settings: Settings):
        self.url = settings.THUNDER_URL.rstrip() if settings.THUNDER_URL else None
        self.file_id = settings.THUNDER_FILE_ID
        self.authorization = settings.THUNDER_AUTHORIZATION
        self.device_id = self.get_device_id()

    def get_pan_auth(self):
        try:
            index_url = f"{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/"
            headers = {
                "Authorization": self.authorization
            }
            response = requests.get(index_url, headers=headers)
            if response.status_code == 200:
                pattern = r'uiauth\(.*?\)\s*{\s*return\s*"([^"]+)"'
                match = re.search(pattern, response.text)
                return match.group(1)
            else:
                logger.error(f"获取迅雷授权code失败:{response.status_code}")
        except Exception as e:
            logger.error(f"获取迅雷授权code失败:{e}")

    def get_device_id(self):
        if self.url:
            try:
                headers = {
                    'pan-auth': self.get_pan_auth(),
                    "Authorization": self.authorization
                }
                response = requests.get(
                    f'{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/tasks?type=user%23runner&device_space=',
                    headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('error', None):
                        logger.error(f"获取迅雷设备ID失败:{data['error']}")
                    else:
                        device_id = data['tasks'][0]['params']['target']
                        return device_id
                else:
                    logger.error(f"获取迅雷设备ID失败:{response.status_code}")
            except Exception as e:
                logger.error(f"获取迅雷设备ID失败:{e}")
        return None

    def analyze_size(self, magnet):
        if self.url:
            list_url = f"{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/resource/list"
            data = {
                "page_size": 1000,
                "urls": magnet
            }
            headers = {
                'pan-auth': self.get_pan_auth(),
                "Authorization": self.authorization
            }
            logger.info(f"开始解析磁力链接:{magnet}")
            response = requests.post(list_url, json=data, headers=headers)
            if response.status_code == 200:
                files = response.json()
                resources = files['list']['resources'][0]['dir']['resources']
                filter_resources = []
                for index, resource in enumerate(resources):
                    if resource['file_size'] > 1000000000:
                        filter_resources.append(resource)
                file_size = 0
                for resource in filter_resources:
                    logger.info(f"文件名：{resource['name']},文件大小：{resource['file_size'] / 1024 / 1024}MB")
                    file_size += resource['file_size']
                return file_size / 1024 / 1024
            else:
                logger.error(f"解析磁力链接失败:{response.status_code}")
        return 0

    def download(self, magnet):
        if self.url and self.file_id and self.device_id:
            list_url = f"{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/resource/list"
            data = {
                "page_size": 1000,
                "urls": magnet
            }
            pan_auth = self.get_pan_auth()
            headers = {
                'pan-auth': pan_auth,
                "Authorization": self.authorization
            }
            logger.info(f"开始解析磁力链接:{magnet}")
            response = requests.post(list_url, json=data, headers=headers)
            if response.status_code == 200:
                files = response.json()
                file_name = files['list']['resources'][0]['name']
                logger.info(f"种子名称：{file_name}")
                logger.info(f"文件列表：")
                resources = files['list']['resources'][0]['dir']['resources']
                indexs = []
                filter_resources = []
                for index, resource in enumerate(resources):
                    logger.info(f"文件名：{resource['name']},文件大小：{resource['file_size'] / 1024 / 1024}MB")
                    if resource['file_size'] > 1000000000:
                        indexs.append(str(index))
                        filter_resources.append(resource)
                logger.info(f"过滤1GB大小文件列表：")
                file_size = 0
                for resource in filter_resources:
                    logger.info(f"文件名：{resource['name']},文件大小：{resource['file_size'] / 1024 / 1024}MB")
                    file_size += resource['file_size']
                task_url = f"{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/task"
                data = {
                    "params": {
                        "parent_folder_id": self.file_id,
                        "url": magnet,
                        "target": self.device_id,
                        "total_file_count": str(len(resources)),
                        "sub_file_index": ','.join(indexs)
                    },
                    "file_name": file_name,
                    "file_size": str(file_size),
                    "name": file_name,
                    "type": "user#download-url",
                    "space": self.device_id,
                }
                logger.info(f"开始添加迅雷下载")
                response = requests.post(task_url, json=data, headers=headers)
                if response.status_code == 200:
                    logger.info("添加迅雷成功")
                    return True
                else:
                    logger.error(f"添加迅雷失败:{response.status_code}")
            else:
                logger.error(f"解析磁力链接失败:{response.status_code}")
        return False


if __name__ == '__main__':
    thunder = Thunder(get_settings())
    thunder.download('magnet:?xt=urn:btih:7457A4ED150F0F843A64914B22794650EB3BDE13')
    thunder.download('magnet:?xt=urn:btih:6D31DAC042C44B6A53D600E80A00C1BD50DE8E44')
    thunder.download('magnet:?xt=urn:btih:F135E9AD57231BF206898E639A4A33E15A17D250')
    thunder.download('magnet:?xt=urn:btih:4B2D291D2EE8A454C6A716754DF0C7EDA6878B90')