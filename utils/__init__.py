import os
import re
import threading
import time
import urllib
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse
from torrentool.torrent import Torrent
from fake_useragent import UserAgent

from app.utils.log import logger


def date_str_to_timestamp(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        timestamp = date.strftime('%Y%m%d')
        return int(timestamp)
    except Exception as e:
        return None


def dict_trans_obj(source: Dict, target: object):
    if not source:
        return
    if not target or not target.__annotations__:
        return
    for name in target.__annotations__:
        setattr(target, name, source.get(name))


def copy_properties(source: object, target: object) -> None:
    if not source:
        return
    if not target or not target.__annotations__:
        return
    for name in target.__annotations__:
        setattr(target, name, getattr(source, name))


def run_in_background(task_func, *args):
    process = threading.Thread(target=task_func, args=args)
    process.daemon = True  # 设置为守护进程，这样主程序结束时它会自动结束
    process.start()


def get_filename_from_url(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    return path_parts[-1]


def check_file_exists(directory, filename):
    # 构造完整文件路径
    file_path = os.path.join(directory, filename)
    # 检查文件是否存在
    return os.path.isfile(file_path)


def get_host_and_port(url):
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port

    # 如果端口号为空，则根据方案设置默认端口
    if port is None:
        if parsed_url.scheme == 'http':
            port = 80
        elif parsed_url.scheme == 'https':
            port = 443

    return host, port


def to_cookie_dict(cookie_str):
    cookies = {}
    for cookie in cookie_str.split(';'):
        name, value = cookie.strip().split('=', 1)
        cookies[name] = value
    return cookies


def has_number(keyword):
    for s in keyword:
        if s.isdigit():
            return True
    else:
        return False


def is_code(s):
    pattern = r'^[A-Za-z]+-?\d+$'
    return bool(re.fullmatch(pattern, s))


def get_true_code(input_code: str):
    if is_code(input_code):
        code_list = input_code.split('-')
        code = ''.join(code_list)
        length = len(code)
        index = length - 1
        num = ''
        all_number = '0123456789'
        while index > -1:
            s = code[index]
            if s not in all_number:
                break
            num = s + num
            index = index - 1
        prefix = code[0:index + 1]
        if prefix:
            return (prefix + '-' + num).upper()
    return None


def get_protocol_and_domain(url):
    parsed_url = urlparse(url)
    protocol = parsed_url.scheme
    domain = parsed_url.netloc
    return protocol, domain


def find_serial_number(title):
    # 正则表达式匹配格式为字母-数字的模式
    pattern = r'[A-Za-z]+-\d+'
    matches = re.findall(pattern, title)
    if matches:
        return matches[0].upper()
    return None


def unique_objects_by_attribute(objects, attribute):
    seen = set()
    unique = []
    for obj in objects:
        # 检查属性值是否已经出现过
        val = getattr(obj, attribute, None)
        if val not in seen:
            seen.add(val)
            unique.append(obj)
    return unique


def timer(name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            display_name = name if name is not None else func.__name__
            logger.info(f"{display_name}耗时: {(end_time - start_time) * 1000:.0f} 毫秒")
            return result

        return wrapper

    return decorator


def timer_count():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            return result, round((end_time - start_time) * 1000, 0)
        return wrapper

    return decorator


def get_torrent_hash(torrent_path):
    try:
        info = Torrent.from_file(torrent_path)
        return info.info_hash
    except Exception as e:
        logger.error(e)
        return None


def safe_map_url_to_filesystem(url, base_dir="/data/temp", create_dirs=False):

    parsed = urllib.parse.urlparse(url)

    # 获取域名并清理特殊字符
    domain = parsed.netloc
    if not domain:
        domain = "_no_domain"
    else:
        domain = domain.replace(':', '_').replace('/', '_')

    path = parsed.path.strip('/')
    path = path.replace(':', '_').replace('?', '_').replace('*', '_')
    full_path = Path(base_dir) / domain / path
    if create_dirs:
        dir_part = full_path.parent
        dir_part.mkdir(parents=True, exist_ok=True)

    return full_path


def get_image_suffix_from_url(url: str) -> str | None:

    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    suffix = os.path.splitext(filename)[1].lstrip('.').lower()

    common_image_suffixes = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "svg", "ico"}
    if suffix in common_image_suffixes:
        return suffix
    return None


# 测试用例

ua = UserAgent()
