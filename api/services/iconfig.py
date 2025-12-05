import json
import os

import requests
from dotenv import load_dotenv, set_key, dotenv_values

from app.modules import load_module
from app.schemas.reponse import ResponseEntity
from app.schduler import restart_scheduler
from app.core.config import env_path, Settings, load_settings, get_settings, log_dir
from app.utils.log import logger
from app.version import AL_VERSION


def get_config() -> ResponseEntity:
    settings = get_settings()
    config = settings.to_safe_dict()
    config['DEFAULT_SORT'] = config['DEFAULT_SORT'].split(',')
    return ResponseEntity(success=True, message="配置", data=config)


def save_config(config: Settings) -> ResponseEntity:
    safe_config = config.to_safe_dict()
    safe_config['DEFAULT_FILTER'] = json.dumps(safe_config['DEFAULT_FILTER'])
    safe_config['DEFAULT_SORT'] = ','.join(safe_config['DEFAULT_SORT'])
    app_config = dotenv_values(env_path)
    load_dotenv(env_path)
    reload_schedule = False
    create_bot = False
    for key, value in safe_config.items():
        if key in app_config and app_config[key] != value:
            set_key(env_path, key, str(value))
            del os.environ[key]
            if key in ['RANK_SCHEDULE_TIME', 'ACTOR_SCHEDULE_TIME', 'DOWNLOAD_SCHEDULE_TIME', 'QBITTORRENT_URL',
                       'QBITTORRENT_USERNAME', 'QBITTORRENT_PASSWORD', 'TRANSMISSION_URL', 'TRANSMISSION_USERNAME',
                       'TRANSMISSION_PASSWORD']:
                reload_schedule = True
            # if key in ['TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID','TELEGRAM_SPOILER','TELEGRAM_WHITELIST']:
            #     create_bot = True
    load_settings()
    load_module()

    if reload_schedule:
        restart_scheduler()
    # if create_bot:
    #     return ResponseEntity(success=True, message="保存配置成功,检测到telegram TOKEN发生变化,请重启docker")
    return ResponseEntity(success=True, message="保存配置成功")


def sort_tags(tags: list):
    return sorted(tags, key=lambda x: int(x.split('.')[0]))


def get_latest_version():
    try:
        settings = get_settings()
        url = "https://hub.docker.com/v2/repositories/envyafish/byte-muse/tags/"
        proxies = {
            "http": settings.PROXY,
            "https": settings.PROXY
        }
        res = requests.get(url, proxies=proxies, timeout=10)
        res.raise_for_status()  # Raise an exception for bad status codes
        tags = res.json().get("results", [])
        sorted_tags = sort_tags(
            tag['name'] for tag in tags if 'latest' not in tag['name'] and 'beta' not in tag['name'])
        latest_tag = sorted_tags[0] if sorted_tags else AL_VERSION
        return latest_tag, []
    except Exception as e:
        logger.error(f"获取最新版本失败: {e}")
        return None, []


def get_logs(lines: int = 100):
    if not os.path.exists(os.path.join(log_dir, "app.log")):
        return ResponseEntity(success=False, message="日志文件不存在", data="")
    try:
        with open(os.path.join(log_dir, "app.log"), 'r', encoding='utf-8') as file:
            return file.readlines()[-lines:]
    except Exception as e:
        return ResponseEntity(success=False, message=f"读取日志失败: {e}", data="")


def get_bypass_status():
    settings = get_settings()
    res = requests.get(f"{settings.BYPASS_URL}/cookies?url=https://nopecha.com/demo/cloudflare", timeout=30)
    if res.ok:
        return True
    else:
        return False
