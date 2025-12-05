import threading
import time

import qbittorrentapi

from app.database.models.health import Health
from app.core.config import Settings, get_settings
from app.utils import timer_count
from app.utils.log import logger


class QBitTorrentClient:
    client = None
    url: str = None
    username: str = None
    password: str = None
    thread: threading.Thread = None
    anti_leech: bool = True

    def __init__(self, settings: Settings):
        self.url = settings.QBITTORRENT_URL
        self.username = settings.QBITTORRENT_USERNAME
        self.password = settings.QBITTORRENT_PASSWORD
        self.anti_leech = settings.ENABLE_BT_ANTI_LEECH
        self.login_qb()

    def login_qb(self):
        if self.url and self.username and self.password:
            self.client = qbittorrentapi.Client(
                host=self.url,
                username=self.username,
                password=self.password
            )
            try:
                self.client.auth_log_in()
                return True
            except Exception as e:
                logger.error(f"qBittorrent连接失败: {e}")
        return False

    def add_torrent(self, torrent_file_path, save_path=None, category=None, tags=None):
        if self.login_qb():
            try:
                with open(torrent_file_path, 'rb') as f:
                    self.client.torrents_add(
                        torrent_files=f,
                        save_path=save_path,
                        category=category,
                        tags=tags
                    )
                return True
            except Exception as e:
                logger.error(f"添加种子失败: {torrent_file_path},{e}")
        return False

    def add_torrent_by_magnet(self, magnet, save_path=None, category=None, tags=None, min_size_mb=1000):
        if self.login_qb():
            try:
                self.client.torrents_add(urls=magnet,
                                         save_path=save_path,
                                         category=category,
                                         seeding_time_limit=0 if self.anti_leech else None,
                                         tags=tags)
                torrent_hash = magnet.split('btih:')[1].split('&')[0].lower()
                max_retries = 10
                retries = 0
                files_info = []

                while retries < max_retries:
                    try:
                        files_info = self.client.torrents_files(torrent_hash)
                        if files_info:
                            break
                    except Exception as e:
                        logger.error(f"获取文件信息出错: {e}")
                    time.sleep(6)
                    retries += 1

                if not files_info:
                    logger.error("无法获取文件信息")
                    return False
                small_file_ids = []
                for file_info in files_info:
                    file_size_mb = file_info['size'] / (1024 * 1024)
                    if file_size_mb < min_size_mb:
                        small_file_ids.append(file_info['index'])
                        logger.info(f"标记不下载: {file_info['name']} ({file_size_mb:.2f}MB)")

                if small_file_ids:
                    self.client.torrents_file_priority(torrent_hash, small_file_ids, 0)
                    logger.info(f"已设置 {len(small_file_ids)} 个小文件不下载")
                else:
                    logger.info("没有需要过滤的小文件")
                return True
            except Exception as e:
                logger.error(f"下载磁链失败:{e}")
                return False
        return False

    def monitor_torrent(self):
        from app.services import send_downloaded_message
        torrents = self.client.torrents_info()
        for torrent in torrents:
            if torrent.progress == 1.0 and 'BYTE_MUSE' in torrent.tags and '已完成' not in torrent.tags:
                self.client.torrents_add_tags(tags=['BYTE_MUSE', '已完成'], torrent_hashes=[torrent.hash])
                send_downloaded_message(torrent.name, torrent.save_path, torrent.hash)

    @timer_count()
    def healthy_check(self):
        if self.url and self.username and self.password:
            self.client = qbittorrentapi.Client(
                host=self.url,
                username=self.username,
                password=self.password
            )
            try:
                self.client.auth_log_in()
                return Health({"module": "QBITTORRENT", "status": "healthy", "info": "success"})
            except Exception as e:
                return Health({"module": "QBITTORRENT", "status": "unhealthy", "info": "fail"})
        return Health({"module": "QBITTORRENT", "status": "none", "info": "none"})


if __name__ == '__main__':
    qb = QBitTorrentClient(get_settings())
    qb.add_torrent_by_magnet('magnet:?xt=urn:btih:F135E9AD57231BF206898E639A4A33E15A17D250','/video/学习资料/日语学习','','BYTE_MUSE',1000)