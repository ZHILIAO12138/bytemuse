import aria2p
import time

from app.core.config import Settings, get_settings


class Aria2:
    def __init__(self, settings: Settings):
        if settings.ARIA_URL and settings.ARIA_SECRET:
            self.aria2 = aria2p.API(
                aria2p.Client(
                    host=settings.ARIA_URL,
                    port=6800,
                    secret=settings.ARIA_SECRET,
                )
            )

    def wait_for_metadata(self, download, timeout=60):
        """等待元数据获取完成"""
        start_time = time.time()
        while not download.followed_by_ids:
            if time.time() - start_time > timeout:
                raise TimeoutError("获取元数据超时")
            time.sleep(1)
            download.update()
        return True

    def filter_small_files(self, download, min_size_mb):
        """过滤小文件"""
        sub_downloads = []
        for gid in download.followed_by_ids:
            try:
                sub = self.aria2.get_download(gid)
                sub.update()
                sub_downloads.append(sub)
            except Exception as e:
                print(f"获取子任务 {gid} 失败: {e}")
                continue

        for sub in sub_downloads:
            try:
                file_size_mb = sub.total_length / (1024 * 1024)
                if file_size_mb < min_size_mb:
                    print(f"过滤小文件: {sub.name} ({file_size_mb:.2f} MB)")
                    sub.remove(force=True)
                else:
                    print(f"保留文件: {sub.name} ({file_size_mb:.2f} MB)")
            except Exception as e:
                print(f"处理文件 {sub.name if hasattr(sub, 'name') else '未知'} 失败: {e}")

    def download_magnet_with_filter(self, magnet_uri, min_size_mb=100, options=None):
        """
        下载磁力链接并过滤小文件

        :param magnet_uri: 磁力链接
        :param min_size_mb: 最小文件大小(MB)
        :param options: 额外下载选项
        """
        options = options or {}

        try:
            # 添加磁力链接
            download = self.aria2.add_magnet(magnet_uri, options=options)
            print(f"已添加磁力链接，GID: {download.gid}")

            # 等待获取元数据
            print("等待获取元数据...")
            self.wait_for_metadata(download)

            # 过滤小文件
            print("开始过滤小文件...")
            self.filter_small_files(download, min_size_mb)

            print("下载任务已开始，保留的文件将被下载")
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False


if __name__ == '__main__':
    downloader = Aria2(get_settings())

    # 下载选项
    options = {
        "dir": "/vol1/1000/video/aria2",  # 下载目录
        "max-connection-per-server": "16",
        "seed-ratio": "1.0",  # 分享率达到1.0后停止
        "bt-save-metadata": "true"  # 保存元数据
    }

    magnet_link = "magnet:?xt=urn:btih:4B2D291D2EE8A454C6A716754DF0C7EDA6878B90"
    downloader.download_magnet_with_filter(
        magnet_link,
        min_size_mb=1000,  # 过滤小于100MB的文件
        options=options
    )
