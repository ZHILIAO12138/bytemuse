import os
import secrets
import shutil
import string
from pathlib import Path

import dotenv
from dotenv import dotenv_values, set_key
from pydantic import BaseSettings


def copy_env(template_path, app_env_path):
    if not os.path.exists(env_path):
        os.makedirs(os.path.dirname(app_env_path), exist_ok=True)
        shutil.copy(env_template_path, env_path)
    else:
        template_config = dotenv_values(template_path)
        app_config = dotenv_values(app_env_path)
        for key, value in template_config.items():
            if key not in app_config:
                set_key(app_env_path, key, value)


def generate_secure_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(letters) for i in range(length))


root_path = '/' if os.environ.get('DOCKER_ENV') else os.path.dirname(Path(__file__).resolve().parent.parent)
env_template_path = os.path.join(root_path, 'app', 'core', '.env.example')
data_path = os.path.join(root_path, 'data')
env_path = os.path.join(data_path, 'app.env')
copy_env(env_template_path, env_path)
torrent_folder = os.path.join(data_path, 'torrents')
db_path = os.path.join(data_path, 'lady.db')
temp_folder = os.path.join(data_path, 'temp')
log_dir = os.path.join(data_path, 'logs')
DATABASE_PATH = f'sqlite:///{db_path}'  # 数据库地址
app_config = dotenv_values(env_path)
if "SECRET_KEY" not in app_config or not app_config['SECRET_KEY']:
    random_str = generate_secure_random_string(32)
    set_key(env_path, "SECRET_KEY", random_str)


class Settings(BaseSettings):
    # 定时程序配置
    RANK_SCHEDULE_TIME: str | None
    ACTOR_SCHEDULE_TIME: str | None
    DOWNLOAD_SCHEDULE_TIME: str | None
    RANK_PAGE: str | None
    RANK_TYPE: str | None
    BRAND_TYPE: str | None
    # 用户配置
    EMBY_URL: str | None  # Emby服务器地址
    EMBY_API_KEY: str | None  # Emby API Key
    PLEX_URL: str | None  # Plex服务器
    PLEX_TOKEN: str | None  # Plex Token
    JELLYFIN_URL: str | None  # Jellyfin服务器
    JELLYFIN_API_KEY: str | None  # Jellyfin API Key
    JELLYFIN_USER: str | None  # Jellyfin用户
    QBITTORRENT_URL: str | None  # qBittorrent服务器地址
    QBITTORRENT_USERNAME: str | None  # qBittorrent用户名
    QBITTORRENT_PASSWORD: str | None  # qBittorrent密码
    QBITTORRENT_DOWNLOAD_PATH: str | None  # qBittorrent下载路径
    QBITTORRENT_CATEGORY: str | None
    TRANSMISSION_URL: str | None
    TRANSMISSION_USERNAME: str | None
    TRANSMISSION_PASSWORD: str | None
    TRANSMISSION_DOWNLOAD_PATH: str | None
    TRANSMISSION_LABEL: str | None
    THUNDER_URL: str | None
    THUNDER_FILE_ID: str | None
    THUNDER_AUTHORIZATION: str | None
    NICEPT_COOKIE: str | None  # NICEPT cookie
    ROUSI_COOKIE: str | None  # Rousi cookie
    PTT_COOKIE: str | None  # Rousi cookie
    MTEAM_API_KEY: str | None  # 馒头API Key
    LIBRARY_COOKIE: str | None
    BUS_COOKIE: str | None
    AVDB_COOKIE: str | None
    AVBASE_COOKIE: str | None
    WECHAT_CORP_ID: str | None  # 微信企业ID
    WECHAT_CORP_SECRET: str | None  # 微信企业密钥
    WECHAT_AGENT_ID: str | None  # 微信应用ID
    WECHAT_TOKEN: str | None  # 微信Token
    WECHAT_ENCODING_AES_KEY: str | None
    WECHAT_TO_USER: str | None
    WECHAT_PROXY: str | None  # 微信代理
    WECHAT_PHOTO: str | None
    WECHAT_BANNER: bool | None
    TELEGRAM_BOT_TOKEN: str | None  # Telegram Bot Token
    TELEGRAM_CHAT_ID: str | None  # Telegram Chat ID
    TELEGRAM_SPOILER: bool | None
    TELEGRAM_WHITELIST: str | None
    PROXY: str | None  # HTTP代理
    DEFAULT_FILTER: str | dict | None  # 过滤器
    DEFAULT_SORT: str | list | None  # 排序
    IMAGE_MODE: str | None
    FLARE_SOLVERR_URL: str | None
    SECRET_KEY: str | None
    MAIN_SITE: str | None
    MAX_ACTOR: str | None
    BYPASS_URL: str | None
    CLOUDNAS_URL: str | None
    CLOUDNAS_USERNAME: str | None
    CLOUDNAS_PASSWORD: str | None
    CLOUDNAS_SAVEPATH: str | None
    NICKNAME: str | None
    ARIA_URL: str | None
    ARIA_SECRET: str | None
    ENABLE_BT: bool | None
    ENABLE_BT_ANTI_LEECH: bool | None
    SHT_DB: str | None
    ENABLE_PHOTO_CACHE: bool | None

    class Config:
        env_file = os.path.join(env_path)

    def to_safe_dict(self):
        # 要排除的敏感字段
        exclude_fields = {"SECRET_KEY"}
        return {k: v for k, v in self.__dict__.items() if k not in exclude_fields}


_settings = None


def load_settings():
    global _settings
    dotenv.load_dotenv(env_path)
    _settings = Settings()
    return _settings


def get_settings():
    global _settings
    if _settings is None:
        return load_settings()
    return _settings
