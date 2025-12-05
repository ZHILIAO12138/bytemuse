import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

from sqlalchemy.orm import Session

from app.schemas.torrent import Torrent
from app.database.models import Code, Actor
from app.database.models.history import History
from app.database.session import session_scope
from app.modules import get_module
from app.core.config import get_settings
from app.utils import find_serial_number, get_torrent_hash
from app.utils.filters import filter_torrents, sort_torrents
from app.utils.log import logger


def is_exist_server(code_no: str):
    module = get_module()
    if module.emby.search(code_no):
        return True
    if module.plex.search(code_no):
        return True
    if module.jellyfin.search(code_no):
        return True
    return False


def search_code(code_no: str):
    module = get_module()
    codes, actors = module.avbase.search_keyword(code_no)
    if codes:
        code = codes[0]
        code.code = code_no
        return code
    code = module.bus.search(code_no)
    if code:
        code.code = code_no
        return code
    code = module.avdb.search(code_no)
    if code:
        code.code = code_no
        return code
    return None


def find_torrent(code: Code, torrents: List[Torrent]):
    logger.info(f"开始过滤{code.code}的资源,订阅模式:{code.mode}")
    settings = get_settings()
    filter_str = code.filter if code.filter else json.dumps(settings.DEFAULT_FILTER)
    sort = settings.DEFAULT_SORT
    filter = json.loads(filter_str)
    logger.info(f"过滤器:{filter}")
    sort_list = sort.split(',')
    logger.info(f"排序:{sort_list}")
    is_pass_filter = False
    pre_torrents = filter_torrents(torrents, filter)
    if pre_torrents:
        is_pass_filter = True
    if code.mode == 'STRICT':
        torrents = filter_torrents(torrents, filter)
        torrents = sort_torrents(torrents, sort_list, settings.MAIN_SITE)
    else:
        if is_pass_filter:
            torrents = sort_torrents(pre_torrents, sort_list, settings.MAIN_SITE)
        else:
            torrents = sort_torrents(torrents, sort_list, settings.MAIN_SITE)
    if not torrents:
        return [], is_pass_filter
    return torrents[0], is_pass_filter


def run_sub(code_no: str):
    logger.info(f"开始搜索种子资源:{code_no}")
    module = get_module()
    settings = get_settings()
    with session_scope() as session:
        code = session.get(Code, code_no)
        torrents = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_mteam = executor.submit(module.mteam.search, code.code)
            future_ptt = executor.submit(module.ptt.search, code.code)
            future_nicept = executor.submit(module.nicept.search, code.code)
            future_rousi = executor.submit(module.rousi.search, code.code)
            future_sht = executor.submit(module.sht.search, code.code)
            results = []
            for future in [future_mteam, future_ptt, future_nicept, future_rousi, future_sht]:
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"搜索失败: {str(e)}")
                    results.append([])
        mteam_torrents, ptt_torrents, nicept_torrents, rousi_torrents, sht_torrents = results
        torrents.extend(mteam_torrents + ptt_torrents + nicept_torrents + rousi_torrents + sht_torrents)
        logger.info(f"已搜索到{code_no}的种子资源:{torrents}")
        torrent, is_pass_filter = find_torrent(code, torrents)
        if torrent:
            logger.info(f"过滤完成，得到{code_no}的种子资源：{torrent},即将开始下载种子文件")
            torrent_path = None
            if torrent.site == module.mteam.site_name:
                torrent_path = module.mteam.download_seed(torrent)
            elif torrent.site == module.nicept.site_name:
                torrent_path = module.nicept.download_seed(torrent)
            elif torrent.site == module.ptt.site_name:
                torrent_path = module.ptt.download_seed(torrent)
            elif torrent.site == module.rousi.site_name:
                torrent_path = module.rousi.download_seed(torrent)
            elif torrent.site == module.sht.site_name:
                torrent_path = torrent.download_url
            if torrent_path:
                if download_torrent(torrent_path):
                    logger.info(f"成功添加{torrent_path}到下载器,订阅完成")
                    if code.mode == 'STRICT':
                        code.status = 'COMPLETE'
                        threading.Thread(target=lambda: send_complete_message(code.banner, code_no, torrent)).start()
                    else:
                        if is_pass_filter:
                            code.status = 'COMPLETE'
                        else:
                            code.mode = 'STRICT'
                            threading.Thread(
                                target=lambda: send_brush_message(code.code, code.title, code.banner)).start()
                    session.commit()
                    session.refresh(code)
                    if not torrent_path.startswith("magnet"):
                        torrent_hash = get_torrent_hash(torrent_path)
                        history = session.get(History, torrent_hash)
                        if not history:
                            history = History(data={
                                'hash': torrent_hash,
                                'code': code_no,
                                'save_path': settings.QBITTORRENT_DOWNLOAD_PATH
                            })
                            session.add(history)
                            session.commit()
                else:
                    logger.error(f"种子文件添加下载失败：{torrent_path}")
            else:
                logger.error(f"种子文件下载失败：{torrent}")


def subscribe_code_by_actor(actor: Actor, session: Session):
    module = get_module()
    settings = get_settings()
    codes, actors = module.avbase.search_actor(actor.name)
    cache_actors(actors, session)
    for code in codes:
        code_no = code.code
        db_code = session.get(Code, code_no)
        if not db_code:
            session.add(code)
            session.flush()
            session.commit()
            session.refresh(code)
        code = session.get(Code, code_no)
        if code and code.casts and code.status == 'UN_SUBSCRIBE' and not is_exist_server(
                code_no=code_no) and code.release_date > actor.limit_date and 'VR' not in code.code:
            cast_list = code.casts.split(',')
            if len(cast_list) <= int(settings.MAX_ACTOR):
                code.status = 'SUBSCRIBE'
                session.flush()
                session.commit()
                session.refresh(code)
                threading.Thread(target=lambda: send_subscribe_message(code.code, code.title, code.banner)).start()
            else:
                logger.info(f"{code_no}演员人数超过{settings.MAX_ACTOR}名,不进行订阅")


def download_torrent(torrent_path):
    settings = get_settings()
    module = get_module()
    tr_success = False
    qb_success = False
    thunder_success = False
    cloud_success = False
    if torrent_path.startswith("magnet"):
        thunder_success = module.thunder.download(torrent_path)
        cloud_success = module.cloud_nas.download_offline(torrent_path)
        if not thunder_success and not cloud_success and module.qbittorrent.client and not settings.CLOUDNAS_URL:
            qb_success = module.qbittorrent.add_torrent_by_magnet(magnet=torrent_path,
                                                                  save_path=settings.QBITTORRENT_DOWNLOAD_PATH,
                                                                  category=settings.QBITTORRENT_CATEGORY,
                                                                  tags="BYTE_MUSE")
        if not thunder_success and not cloud_success and module.transmission.client and not settings.CLOUDNAS_URL:
            tr_success = module.transmission.add_torrent_by_magnet(magnet=torrent_path,
                                                                   save_path=settings.TRANSMISSION_DOWNLOAD_PATH,
                                                                   tags="BYTE_MUSE")
    else:
        if module.qbittorrent.client:
            qb_success = module.qbittorrent.add_torrent(torrent_file_path=torrent_path,
                                                        save_path=settings.QBITTORRENT_DOWNLOAD_PATH,
                                                        category=settings.QBITTORRENT_CATEGORY, tags="BYTE_MUSE")
        if module.transmission.client:
            tr_success = module.transmission.add_torrent(torrent_file_path=torrent_path,
                                                         save_path=settings.TRANSMISSION_DOWNLOAD_PATH,
                                                         tags="BYTE_MUSE")
    return qb_success or tr_success or thunder_success or cloud_success


def send_subscribe_message(code, title, banner):
    module = get_module()
    module.wechat.send_photo_message(title=f"番号{code}已加入订阅列表",
                                     content=title, banner=banner)
    module.telegram.send_photo_message(banner, f"番号{code}已加入订阅列表\n{title}")
    pass


def send_subscribe_actor_message(name, limit_date, photo):
    module = get_module()
    module.wechat.send_photo_message(title=f"演员{name}已加入订阅列表",
                                     content=f"将自动订阅{limit_date}之后的番号", banner=photo)
    module.telegram.send_photo_message(photo,
                                       f"演员{name}已加入订阅列表\n将自动订阅{limit_date}之后的番号")
    pass


def send_complete_message(banner, code_no, torrent: Torrent):
    module = get_module()
    settings = get_settings()
    content = f"""站点：{torrent.site}\n标题: {torrent.title}\n大小: {torrent.size_mb}MB\n做种: {torrent.seeders}
    """
    module.wechat.send_photo_message(title=f"番号{code_no}开始下载",
                                     content=content, banner=banner)
    module.telegram.send_photo_message(banner, f"番号{code_no}开始下载\n{content}")
    pass


def send_downloaded_message(torrent_name, save_path, torrent_hash):
    module = get_module()
    banner = ''
    code_no = ''
    with session_scope() as session:
        history = session.get(History, torrent_hash)
        if history:
            code_no = history.code
            if code_no:
                code = session.get(Code, code_no)
                if code:
                    banner = code.banner
    if not code_no:
        code_no = find_serial_number(torrent_name)
        if not code_no:
            code_no = '未识别'

    module.wechat.send_photo_message(title=f"番号{code_no}已完成下载",
                                     content=f"种子名称:{torrent_name}\n保存路径:{save_path}", banner=banner)
    module.telegram.send_photo_message(photo_url=banner,
                                       caption=f"番号{code_no}已完成下载\n种子名称:{torrent_name}\n保存路径:{save_path}")
    pass


def send_brush_message(code, title, banner):
    module = get_module()
    module.wechat.send_photo_message(title=f"番号{code}已完成初次下载,进入严格模式", content=title, banner=banner)
    module.telegram.send_photo_message(banner, f"番号{code}已完成初次下载,进入严格模式\n{title}")
    pass


def reply_text_msg(channel, msg):
    module = get_module()
    if channel == 'wx':
        module.wechat.send_text_message(content=msg)
    if channel == 'tg':
        module.telegram.send_text_message(text=msg)


def cache_actors(actors, session: Session):
    if actors:
        for actor in actors:
            db_actor = session.get(Actor, actor.name)
            if not db_actor:
                session.add(actor)
                session.commit()
                session.refresh(actor)
