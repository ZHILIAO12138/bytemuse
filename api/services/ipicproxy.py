import io
import os

import requests
from app.core.config import temp_folder, get_settings
from starlette.responses import StreamingResponse, FileResponse

from app.utils import get_filename_from_url, check_file_exists
from app.utils.log import logger


def image_proxy(url: str):
    settings = get_settings()
    filename = get_filename_from_url(url)
    filepath = os.path.join(temp_folder, filename)
    if check_file_exists(temp_folder, filename):
        return FileResponse(filepath, media_type='image/jpeg')
    proxies = {
        "http": settings.PROXY,
        "https": settings.PROXY
    }
    headers = {
        'Referer': 'https://www.javbus.com/'
    }
    try:
        response = requests.get(url, proxies=proxies, headers=headers, timeout=10)
        if response.ok:
            with open(filepath, 'wb') as out_file:
                out_file.write(response.content)
            return StreamingResponse(io.BytesIO(response.content),
                                     media_type=response.headers.get('content-type', 'image/jpeg'))
        else:
            logger.error(f"下载图片失败：{response.status_code}")
    except Exception as e:
        logger.error(f"下载图片失败：{e}")
    return url
