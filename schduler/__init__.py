import json
import os
import random
import threading
import traceback
from datetime import datetime, timedelta

from curl_cffi import requests
import time

from sqlalchemy import desc
from sqlalchemy.sql.operators import isnot

from app import services, utils
from app.database.models import Code, Actor, Cache
from app.database.session import session_scope
from app.modules import get_module
from app.core.config import temp_folder, get_settings, data_path
from app.utils import get_filename_from_url, check_file_exists, get_image_suffix_from_url
from app.utils.log import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


def sub_rank():
    settings = get_settings()
    library_rank = get_library_rank()
    avdb_rank = get_avdb_rank()
    brands_rank = get_brands_rank()
    rank = list(set(library_rank + avdb_rank + brands_rank))
    with session_scope() as session:
        for code_no in rank:
            code = session.get(Code, code_no)
            if code:
                if code.status == 'UN_SUBSCRIBE':
                    code.filter = json.dumps(settings.DEFAULT_FILTER)
                    code.status = 'SUBSCRIBE'
                    if services.is_exist_server(code_no):
                        logger.info(f"{code.code}已存在服务器，自动标记为完成")
                        code.status = 'COMPLETE'
                    if code.status == 'SUBSCRIBE':
                        threading.Thread(target=lambda: services.send_subscribe_message(code.code, code.title,
                                                                                        code.banner)).start()
                    session.commit()
                    session.refresh(code)
            else:
                code = services.search_code(code_no)
                if code:
                    code.filter = json.dumps(settings.DEFAULT_FILTER)
                    code.status = 'SUBSCRIBE'
                    if services.is_exist_server(code_no):
                        logger.info(f"{code.code}已存在服务器，自动标记为完成")
                        code.status = 'COMPLETE'
                    if code.status == 'SUBSCRIBE':
                        threading.Thread(target=lambda: services.send_subscribe_message(code.code, code.title,
                                                                                        code.banner)).start()
                        session.add(code)
                        session.commit()
                        session.refresh(code)


def get_library_rank():
    settings = get_settings()
    module = get_module()
    ranks = []
    if settings.RANK_PAGE and int(settings.RANK_PAGE) > 0:
        with session_scope() as session:
            for i in range(1, int(settings.RANK_PAGE) + 1):
                rank = module.library.crawling_top20(i)
                if not rank:
                    time.sleep(random.randint(1, 600))
                    rank = module.shared.get_shared_rank(i)
                if rank:
                    ranks.extend(rank)
                    rank_cache = Cache({"namespace": 'rank', "key": str(i), "content": ','.join(rank)})
                    session.add(rank_cache)
                    session.commit()
    return ranks


def get_avdb_rank():
    settings = get_settings()
    module = get_module()
    ranks = []
    if settings.RANK_TYPE and settings.RANK_TYPE:
        rank_types = settings.RANK_TYPE.split(',')
        with session_scope() as session:
            for rank_type in rank_types:
                if rank_type in ['daily', 'weekly', 'monthly']:
                    rank = module.avdb.crawling_top(settings.RANK_TYPE)
                    if not rank:
                        time.sleep(random.randint(1, 600))
                        rank = module.shared.get_shared_rank(settings.RANK_TYPE)
                    if rank:
                        rank_cache = Cache({"namespace": 'rank', "key": settings.RANK_TYPE, "content": ','.join(rank)})
                        session.add(rank_cache)
                        session.commit()
                        ranks.extend(rank)
    return ranks


def get_brands_rank():
    settings = get_settings()
    module = get_module()
    ranks = []
    if settings.BRAND_TYPE and settings.BRAND_TYPE:
        brand_types = settings.BRAND_TYPE.split(',')
        with session_scope() as session:
            for brand_type in brand_types:
                if any(brand_type.startswith(prefix) for prefix in
                       ['s1-', 'ip-', 'moodyz-', 'das-', 'madonna-', 'premium-', 'honnaka-', 'attackers-', 'wanz-']):
                    rank = module.brands.get_date_rank(brand_type)
                    if not rank:
                        time.sleep(random.randint(1, 600))
                        rank = module.shared.get_shared_rank(brand_type)
                    if rank:
                        ranks.extend(rank)
                        rank_cache = Cache({"namespace": 'rank', "key": brand_type, "content": ','.join(rank)})
                        session.add(rank_cache)
                        session.commit()
    return ranks


def sync_rank():
    module = get_module()
    time.sleep(random.randint(1, 300))
    logger.info("开始同步榜单数据")
    current_time = datetime.now()
    time_8_hours_ago = current_time - timedelta(hours=24)
    formatted_time_8_hours_ago = time_8_hours_ago.strftime("%Y-%m-%d %H:%M:%S")
    with session_scope() as session:
        ranks = []
        for i in range(1, 6):
            rank_cache = session.query(Cache).filter(Cache.namespace == 'rank').filter(str(i) == Cache.key).filter(
                Cache.create_time >= formatted_time_8_hours_ago).order_by(
                desc(Cache.create_time)).first()
            if rank_cache:
                ranks.extend(rank_cache.content.split(','))
                continue
            rank = module.library.crawling_top20(i)
            if not rank:
                rank = module.shared.get_shared_rank(i)
            if rank:
                ranks.extend(rank)
                rank_cache = Cache({"namespace": 'rank', "key": str(i), "content": ','.join(rank)})
                session.add(rank_cache)
                session.commit()
        for rank_type in ['daily', 'weekly', 'monthly']:
            rank_cache = session.query(Cache).filter(Cache.namespace == 'rank').filter(rank_type == Cache.key).filter(
                Cache.create_time >= formatted_time_8_hours_ago).order_by(
                desc(Cache.create_time)).first()
            if rank_cache:
                ranks.extend(rank_cache.content.split(','))
                continue
            rank = module.avdb.crawling_top(rank_type)
            if not rank:
                rank = module.shared.get_shared_rank(rank_type)
            if rank:
                ranks.extend(rank)
                rank_cache = Cache({"namespace": 'rank', "key": rank_type, "content": ','.join(rank)})
                session.add(rank_cache)
                session.commit()
        for rank_type in ['s1-0', 's1-1', 's1-2', 's1-3', 's1-4', 'ip-0', 'ip-1', 'ip-2', 'ip-3', 'ip-4']:
            rank_cache = session.query(Cache).filter(Cache.namespace == 'rank').filter(rank_type == Cache.key).filter(
                Cache.create_time >= formatted_time_8_hours_ago).order_by(
                desc(Cache.create_time)).first()
            if rank_cache:
                ranks.extend(rank_cache.content.split(','))
                continue
            rank = module.brands.get_date_rank(rank_type)
            if not rank:
                rank = module.shared.get_shared_rank(rank_type)
            if rank:
                ranks.extend(rank)
                rank_cache = Cache({"namespace": 'rank', "key": rank_type, "content": ','.join(rank)})
                session.add(rank_cache)
                session.commit()
        rank_cache = session.query(Cache).filter(Cache.namespace == 'rank').filter("actors" == Cache.key).filter(
            Cache.create_time >= formatted_time_8_hours_ago).order_by(
            desc(Cache.create_time)).first()
        if not rank_cache:
            actor_rank = module.library.crawling_top20_actor()
            if not actor_rank:
                actor_rank = module.shared.get_shared_rank("actors")
            if actor_rank:
                rank_cache = Cache({"namespace": 'rank', "key": "actors", "content": ','.join(actor_rank)})
                session.add(rank_cache)
                session.commit()
                for actor in actor_rank:
                    db_actor = session.get(Actor, actor)
                    if not db_actor:
                        codes, actors = module.avbase.search_actor(actor)
                        services.cache_actors(actors, session)
        codes = []
        for code_no in set(ranks):
            db_code = session.get(Code, code_no)
            if not db_code:
                code = services.search_code(code_no)
                if code:
                    session.add(code)
                    session.flush()
                    session.commit()
                    session.refresh(code)
                    codes.append(code)
            else:
                codes.append(db_code)
        logger.info("榜单同步完成")
        cache_photos(codes, session)


def run_news():
    module = get_module()
    logger.info("开始同步今日上新")
    with session_scope() as session:
        codes = module.avbase.work_date(date=datetime.now().strftime('%Y-%m-%d'))
        for code in codes:
            code_no = code.code
            db_code = session.get(Code, code_no)
            if not db_code:
                session.add(code)
                session.commit()
    logger.info("今日上新同步完成")


def download_un_exist_photo():
    logger.info("开始补充JAVBUS未下载的图片")
    settings = get_settings()
    proxies = {
        "http": settings.PROXY,
        "https": settings.PROXY
    }
    headers = {
        'Referer': 'https://www.javbus.com/'
    }
    with session_scope() as session:
        codes = session.query(Code).all()
        for code in codes:
            protocol, domain = utils.get_protocol_and_domain(code.banner)
            if domain != 'www.javbus.com':
                continue
            try:
                if code.banner:
                    filename = get_filename_from_url(code.banner)
                    filepath = os.path.join(temp_folder, filename)
                    if not check_file_exists(temp_folder, filename):
                        response = requests.get(code.banner, proxies=proxies, headers=headers,  impersonate="chrome110")
                        if response.ok:
                            with open(filepath, 'wb') as out_file:
                                out_file.write(response.content)
            except Exception as e:
                logger.error(f"下载番号{code.code}的图片失败: {e}")


def cache_photos(codes, session):
    settings = get_settings()
    if settings.ENABLE_PHOTO_CACHE:
        logger.info("开始缓存图片")
        for code in codes:
            if code.banner:
                if code.banner.startswith('http'):
                    pic_url = save_image(code.code, code.banner, 'banner')
                    if pic_url:
                        code.banner = pic_url
                        session.flush()
                        session.commit()
                        session.refresh(code)
                        time.sleep(1)
            if code.still_photo:
                still_photos = code.still_photo.split(',')
                pic_urls = []
                for i, still_photo in enumerate(still_photos):
                    if still_photo.startswith('http'):
                        pic_url = save_image(code.code, still_photo, f'still_photo_{i}')
                        if pic_url:
                            pic_urls.append(pic_url)
                        else:
                            pic_urls.append(still_photo)
                if len(pic_urls) > 0:
                    code.still_photo = ','.join(pic_urls)
                    session.flush()
                    session.commit()
                    session.refresh(code)
                    time.sleep(1)
        logger.info("图片缓存完成")


def save_image(code_no, image_url, image_name):
    settings = get_settings()
    proxies = {
        "http": settings.PROXY,
        "https": settings.PROXY
    }
    os.makedirs(os.path.join(data_path, 'pics', code_no), exist_ok=True)
    suffix = get_image_suffix_from_url(image_url)
    if suffix:
        image_name = f"{image_name}.{suffix}"
        image_path = os.path.join(data_path, 'pics', code_no, image_name)
        pic_url = f'/pic/{code_no}/{image_name}'
        if os.path.isfile(image_path):
            return pic_url
        headers = {
            'Referer': 'https://www.javbus.com/'
        }
        try:
            response = requests.get(image_url, proxies=proxies, headers=headers,  impersonate="chrome110")
            if response.ok:
                with open(image_path, 'wb') as out_file:
                    out_file.write(response.content)
                    return pic_url
        except Exception as e:
            logger.error(f"图片下载失败：{image_url},{e}")
            return None
    else:
        logger.error(f"图片后缀获取失败：{image_url}")
    return None


def run_codes():
    one_week_later = datetime.now().date() + timedelta(days=7)
    with session_scope() as session:
        codes = session.query(Code).filter(Code.status == 'SUBSCRIBE').filter(
            Code.release_date <= one_week_later).all()
        session.close()
    for (index, code) in enumerate(codes):
        try:
            services.run_sub(code.code)
            logger.info(f"订阅番号{code.code}已执行完毕")
            if pt_wait():
                if index % 30 == 0:
                    time.sleep(600)
                else:
                    time.sleep(random.randint(60, 180))
        except Exception as e:
            logger.error(f"订阅番号{code.code}失败：{e}")


def pt_wait():
    settings = get_settings()
    if settings.MTEAM_API_KEY or settings.PTT_COOKIE or settings.NICEPT_COOKIE or settings.ROUSI_COOKIE:
        return True
    return False


def run_actors():
    with session_scope() as session:
        actors = session.query(Actor).filter(isnot(Actor.limit_date, None)).all()
        for actor in actors:
            try:
                services.subscribe_code_by_actor(actor, session)
                logger.info(f"订阅演员{actor.name}影片,截止日期{actor.limit_date}已执行完毕")
            except Exception as e:
                logger.error(f"订阅演员{actor.name}失败：{e}")
                traceback.print_exc()


scheduler = BlockingScheduler()


def push_job():
    settings = get_settings()
    module = get_module()
    scheduler.add_job(sync_rank, trigger=CronTrigger.from_crontab(expr="0 */1 * * *"))
    scheduler.add_job(run_news, trigger=CronTrigger(hour=5, minute=0))
    if module.qbittorrent.client:
        scheduler.add_job(module.qbittorrent.monitor_torrent, trigger=CronTrigger.from_crontab(expr="*/5 * * * *"))
    if module.transmission.client:
        scheduler.add_job(module.transmission.monitor_torrent, trigger=CronTrigger.from_crontab(expr="*/5 * * * *"))
    try:
        if settings.RANK_SCHEDULE_TIME:
            scheduler.add_job(sub_rank, trigger=CronTrigger.from_crontab(expr=settings.RANK_SCHEDULE_TIME))

        if settings.ACTOR_SCHEDULE_TIME:
            scheduler.add_job(run_actors, trigger=CronTrigger.from_crontab(expr=settings.ACTOR_SCHEDULE_TIME))

        if settings.DOWNLOAD_SCHEDULE_TIME:
            scheduler.add_job(run_codes, trigger=CronTrigger.from_crontab(expr=settings.DOWNLOAD_SCHEDULE_TIME))
    except Exception as e:
        logger.error(
            "cron表达式错误！至1.10.0版本开始定时程序仅支持5位cron表达式,请前往WEBUI修改,或者修改app.env文件并重启容器")


def start_scheduler():
    push_job()
    scheduler.start()


def restart_scheduler():
    scheduler.remove_all_jobs()
    push_job()


scheduler_thread = threading.Thread(target=lambda: start_scheduler())

if __name__ == '__main__':
    sync_rank()