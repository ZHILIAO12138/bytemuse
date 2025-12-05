import threading
import time

import transmission_rpc

from app import utils
from app.database.models.health import Health
from app.core.config import Settings
from app.utils import timer_count
from app.utils.log import logger


class TransmissionClient:
    client = None
    url: str = None
    username: str = None
    password: str = None
    thread: threading.Thread = None
    anti_leech: bool = True

    def __init__(self, settings: Settings):
        self.url = settings.TRANSMISSION_URL
        self.username = settings.TRANSMISSION_USERNAME
        self.password = settings.TRANSMISSION_PASSWORD
        self.anti_leech = settings.ENABLE_BT_ANTI_LEECH
        self.login_transmission()

    def login_transmission(self):
        if self.url and self.username and self.password:
            host, port = utils.get_host_and_port(self.url)
            try:
                self.client = transmission_rpc.Client(
                    host=host,
                    port=port,
                    username=self.username,
                    password=self.password
                )
                self.client.session_stats()
                return True
            except Exception as e:
                logger.error(f"Transmission连接失败：{e}")
        return False

    def add_torrent(self, torrent_file_path, save_path=None, tags=None):
        if self.login_transmission():
            try:
                with open(torrent_file_path, 'rb') as torrent_file:
                    self.client.add_torrent(torrent=torrent_file, download_dir=save_path, labels=[tags])
                return True
            except Exception as e:
                logger.error(f"添加种子失败{torrent_file_path}: {e}")
        return False

    def add_torrent_by_magnet(self, magnet, save_path=None, tags=None, min_size_mb=1000):
        if self.login_transmission():
            try:
                self.client.add_torrent(torrent=magnet,
                                        download_dir=save_path,
                                        labels=[tags])
                torrent_hash = magnet.split('btih:')[1].split('&')[0].lower()
                max_retries = 10
                retries = 0
                torrent_info = None
                torrent_id = None

                while retries < max_retries:
                    try:
                        torrent_info = self.client.get_torrent(torrent_hash)
                        torrent_id = torrent_info.id
                        if torrent_info:
                            break
                    except Exception as e:
                        logger.error(f"获取文件信息出错: {e}")
                    time.sleep(6)
                    retries += 1

                if not torrent_info:
                    logger.error("无法获取文件信息")
                    return False
                small_file_ids = []
                for file_info in torrent_info.files():
                    file_size_mb = file_info.size / (1024 * 1024)
                    if file_size_mb < min_size_mb:
                        small_file_ids.append(file_info.id)
                        logger.info(f"标记不下载: {file_info.name} ({file_size_mb:.2f}MB)")

                if small_file_ids:
                    self.client.change_torrent(ids=[torrent_id],
                                               files_unwanted=small_file_ids,
                                               seed_ratio_limit=0 if self.anti_leech else None)
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
        torrents = self.client.get_torrents()
        for torrent in torrents:
            if torrent.progress == 100.0 and 'BYTE_MUSE' in torrent.labels and '已完成' not in torrent.labels:
                self.client.change_torrent(labels=['BYTE_MUSE', '已完成'], ids=[torrent.id])
                send_downloaded_message(torrent.name, torrent.download_dir, torrent.hashString)

    @timer_count()
    def healthy_check(self):
        if self.url and self.username and self.password:
            host, port = utils.get_host_and_port(self.url)
            try:
                self.client = transmission_rpc.Client(
                    host=host,
                    port=port,
                    username=self.username,
                    password=self.password
                )
                self.client.session_stats()
                return Health({"module": "TRANSMISSION", "status": "healthy", "info": "success"})
            except Exception as e:
                return Health({"module": "TRANSMISSION", "status": "unhealthy", "info": "fail"})
        return Health({"module": "TRANSMISSION", "status": "none", "info": "none"})
