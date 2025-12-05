import json
import random
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import isnot

from app import services
from app.schemas import Dashboard, CodeQuery, CodeSubscribe, SearchResult
from app.schemas.reponse import ResponseEntity
from app.database.models.cache import Cache
from app.database.models import Code, Actor
from app.database.models.history import History
from app.modules import get_module
from app.schduler import run_codes
from app.core.config import get_settings
from app.services import is_exist_server, run_sub
from app.utils import get_true_code, find_serial_number, timer, get_torrent_hash
from app.schemas.torrent import Torrent as CTorrent, Torrent
from app.utils.log import logger


def dashboard(session) -> ResponseEntity:
    dashboard = Dashboard()
    sub_count = session.query(Code).filter(Code.status == 'SUBSCRIBE').count()
    actor_count = session.query(Actor).filter(isnot(Actor.limit_date, None)).count()
    complete_count = session.query(Code).filter(Code.status == 'COMPLETE').count()
    codes = session.query(Code).filter(Code.status.in_(['SUBSCRIBE', 'COMPLETE'])).all()
    actors = session.query(Actor).filter(isnot(Actor.limit_date, None)).all()
    if actors:
        actor_photo = random_actor_photo(actors)
        dashboard.actor_photo = actor_photo

    cast_list = []
    series_list = []
    publisher_list = []
    for code in codes:
        casts = code.casts
        if casts:
            cast_list.extend(casts.split(','))
        series = code.series
        if series:
            series_list.append(series)
        publisher = code.publisher
        if publisher:
            publisher_list.append(publisher)
    cast_count = Counter(cast_list)
    series_count = Counter(series_list)
    publisher_count = Counter(publisher_list)
    sorted_cast_counted = sorted(cast_count.items(), key=lambda item: item[1], reverse=True)[:10]
    sorted_series_counted = sorted(series_count.items(), key=lambda item: item[1], reverse=True)[:10]
    sorted_publisher_counted = sorted(publisher_count.items(), key=lambda item: item[1], reverse=True)[:10]
    release_today_codes = on_sub_release_today(session)
    dashboard.sub_count = sub_count
    dashboard.actor_count = actor_count
    dashboard.most_actor = sorted_cast_counted
    dashboard.most_series = sorted_series_counted
    dashboard.most_publisher = sorted_publisher_counted
    dashboard.complete_count = complete_count
    dashboard.release_today = release_today_codes
    return ResponseEntity(success=True, message='', data=dashboard.dict())


def random_actor_photo(actors: List[Actor]):
    actor = random.choice(actors)
    if actor.photo:
        return actor.photo
    else:
        return random_actor_photo(actors)


def rank(type: str, session: Session) -> ResponseEntity:
    module = get_module()
    current_time = datetime.now()
    rank = []
    # 计算8小时前的时间
    time_8_hours_ago = current_time - timedelta(hours=24)
    formatted_time_8_hours_ago = time_8_hours_ago.strftime("%Y-%m-%d %H:%M:%S")
    rank_cache = session.query(Cache).filter(Cache.namespace == 'rank').filter(type == Cache.key).filter(
        Cache.create_time >= formatted_time_8_hours_ago).order_by(
        desc(Cache.create_time)).first()
    if rank_cache and rank_cache.content:
        rank = rank_cache.content.split(',')
    else:
        if type in ['daily', 'weekly', 'monthly']:
            rank = module.shared.get_shared_rank(type)
            if not rank:
                rank = module.avdb.crawling_top(type)
        if type in ['1', '2', '3', '4', '5']:
            rank = module.shared.get_shared_rank(type)
            if not rank:
                rank = module.library.crawling_top20(type)
        if any(type.startswith(prefix) for prefix in
               ['s1-', 'ip-', 'moodyz-', 'das-', 'madonna-', 'premium-', 'honnaka-', 'attackers-', 'wanz-']):
            rank = module.shared.get_shared_rank(type)
            if not rank:
                rank = module.brands.get_date_rank(type)
        if rank:
            rank_cache = Cache({"namespace": 'rank', "key": type, "content": ','.join(rank)})
            session.add(rank_cache)
            session.commit()
    for code_no in rank:
        db_code = session.get(Code, code_no)
        if not db_code:
            code = services.search_code(code_no)
            if code:
                session.add(code)
                session.flush()
                session.commit()
                session.refresh(code)
    codes = session.query(Code).filter(Code.code.in_(rank)).all()
    session.close()
    for code in codes:
        setattr(code, 'is_exist_server', services.is_exist_server(code.code))
    # 让返回的顺序和rank的顺序一致
    sorted_codes = sorted(codes, key=lambda x: rank.index(x.code))
    return ResponseEntity(success=True, message=f'榜单', data=sorted_codes)


def code_list(code_query: CodeQuery, session: Session) -> ResponseEntity:
    query = session.query(Code)
    if code_query.status:
        if code_query.status == 'SUBSCRIBE':
            query = query.filter(Code.status == 'SUBSCRIBE')
        if code_query.status == 'COMPLETE':
            query = query.filter(Code.status == 'COMPLETE')
        if code_query.status == 'UN_SUBSCRIBE':
            query = query.filter(Code.status.in_(['UN_SUBSCRIBE', 'CANCEL']))
    if code_query.query:
        query = query.filter(
            func.upper(Code.code + Code.casts + Code.genres + Code.producer + Code.publisher + Code.series).like(
                f'%{code_query.query.upper()}%'))
    total = query.count()
    query = query.order_by(Code.create_time.desc()).offset((code_query.page - 1) * code_query.size).limit(
        code_query.size)

    codes = query.all()
    for code in codes:
        setattr(code, 'is_exist_server', services.is_exist_server(code.code))
    session.close()
    return ResponseEntity(success=True, message='查询成功', data={
        'data': codes,
        'total': total
    })


def recommend(session: Session) -> ResponseEntity:
    # 返回订阅最多的tag，演员，系列
    codes = session.query(Code).filter(Code.status.in_(['SUBSCRIBE', 'COMPLETE'])).all()
    genres_list = []
    cast_list = []
    series_list = []
    publisher_list = []
    weight = {"genres": 0.1, "cast": 0.5, "series": 0.2, "publisher": 0.2}
    for code in codes:
        genres = code.genres
        if genres:
            genres_list.extend(genres.split(','))
        casts = code.casts
        if casts:
            cast_list.extend(casts.split(','))
        series = code.series
        if series:
            series_list.append(series)
        publisher = code.publisher
        if publisher:
            publisher_list.append(publisher)
    genres_count = Counter(genres_list)
    cast_count = Counter(cast_list)
    series_count = Counter(series_list)
    publisher_count = Counter(publisher_list)
    sorted_genres_counted = sorted(genres_count.items(), key=lambda item: item[1], reverse=True)[:10]
    sorted_cast_counted = sorted(cast_count.items(), key=lambda item: item[1], reverse=True)[:10]
    sorted_series_counted = sorted(series_count.items(), key=lambda item: item[1], reverse=True)[:10]
    sorted_publisher_counted = sorted(publisher_count.items(), key=lambda item: item[1], reverse=True)[:10]
    genres_score = {item: 10 - index for index, (item, _) in enumerate(sorted_genres_counted)}
    cast_score = {item: 10 - index for index, (item, _) in enumerate(sorted_cast_counted)}
    series_score = {item: 10 - index for index, (item, _) in enumerate(sorted_series_counted)}
    publisher_score = {item: 10 - index for index, (item, _) in enumerate(sorted_publisher_counted)}
    # 获取当前日期
    current_date = datetime.now()
    previous_month = current_date - relativedelta(months=1)
    next_month = current_date + relativedelta(months=1)
    unsubscribe_codes = session.query(Code).filter(Code.status == 'UN_SUBSCRIBE').filter(
        Code.release_date.between(previous_month.strftime("%Y-%m-%d"), next_month.strftime("%Y-%m-%d"))).all()
    session.close()
    for code in unsubscribe_codes:
        code_weight = 0
        if code.genres:
            for item, score in genres_score.items():
                if item in code.genres:
                    code_weight += score * weight['genres']
        if code.series:
            for item, score in series_score.items():
                if item in code.casts:
                    code_weight += score * weight['series']
        if code.publisher:
            for item, score in publisher_score.items():
                if item in code.publisher:
                    code_weight += score * weight['publisher']
        if code.casts:
            cast_arr = code.casts.split(',')
            if len(cast_arr) <= 3:
                for item, score in cast_score.items():
                    if item in code.casts:
                        code_weight += score * weight['cast']
        setattr(code, "weight", code_weight)
    filtered_data = [item for item in unsubscribe_codes if item.weight > 0]
    recommend_list = sorted(filtered_data, key=lambda item: item.weight, reverse=True)[:48]
    recommend_list = [item for item in recommend_list if not is_exist_server(item.code)]
    for code in recommend_list:
        setattr(code, 'is_exist_server', False)
    return ResponseEntity(success=True, message='查询成功', data=recommend_list)


def release_today(session):
    today_date = datetime.now().strftime('%Y-%m-%d')
    codes = session.query(Code).filter(Code.release_date == today_date).all()
    for code in codes:
        setattr(code, 'is_exist_server', services.is_exist_server(code.code))
    return ResponseEntity(success=True, message='查询成功', data=codes)


def on_sub_release_today(session):
    today_date = datetime.now().strftime('%Y-%m-%d')
    end_date = datetime.now() + timedelta(days=3)
    end = end_date.strftime('%Y-%m-%d')
    codes = (session.query(Code).filter(Code.status == 'SUBSCRIBE')
             .filter(Code.release_date >= today_date)
             .filter(Code.release_date <= end)
             .order_by(Code.release_date.asc())
             .all())
    for code in codes:
        setattr(code, 'is_exist_server', services.is_exist_server(code.code))
    return codes


def sub(subscribe: CodeSubscribe, session: Session) -> ResponseEntity:
    settings = get_settings()
    subscribe.code = subscribe.code.upper()
    code = session.get(Code, subscribe.code)
    code.filter = json.dumps(subscribe.filter) if subscribe.filter else json.dumps(settings.DEFAULT_FILTER)
    status = code.status
    if subscribe.mode:
        code.mode = subscribe.mode
    code.status = 'SUBSCRIBE'
    session.commit()
    if status != 'SUBSCRIBE':
        threading.Thread(target=lambda: services.send_subscribe_message(code.code, code.title, code.banner)).start()
    threading.Thread(target=lambda: services.run_sub(subscribe.code)).start()
    return ResponseEntity(success=True, message='订阅成功')


def cancel(code_no: str, session: Session) -> ResponseEntity:
    code_no = code_no.upper()
    code = session.get(Code, code_no)
    code.status = 'CANCEL'
    session.flush()
    session.commit()
    return ResponseEntity(success=True, message='取消订阅成功')


@timer(name="搜索接口")
def torrents(query: str, session: Session) -> ResponseEntity:
    # 记录耗时
    module = get_module()
    settings = get_settings()
    search_result = SearchResult()
    torrents = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 提交所有搜索任务
        true_code = get_true_code(query)
        if true_code:
            query = true_code
        future_avbase = executor.submit(module.avbase.search_keyword, query)
        future_mteam = executor.submit(module.mteam.search, query)
        future_ptt = executor.submit(module.ptt.search, query)
        future_nicept = executor.submit(module.nicept.search, query)
        future_rousi = executor.submit(module.rousi.search, query)
        future_sht = executor.submit(module.sht.search, query)
        futures_to_process = [future_avbase, future_mteam, future_ptt, future_nicept, future_rousi, future_sht]

        # 统一处理结果和异常
        results = []
        for future in futures_to_process:
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"搜索失败: {str(e)}")
                if future == future_avbase:
                    results.append(([], []))
                else:
                    results.append([])
    avbase_data, mteam_torrents, ptt_torrents, nicept_torrents, rousi_torrents, sht_torrents = results
    torrents.extend(mteam_torrents + ptt_torrents + nicept_torrents + rousi_torrents + sht_torrents)
    codes, actors = avbase_data
    services.cache_actors(actors, session)
    if not codes:
        avdb_code = module.avdb.search(query)
        if avdb_code:
            codes.append(avdb_code)
        else:
            bus_code = module.bus.search(query)
            if bus_code:
                codes.append(bus_code)
    codes_no = [item.code for item in codes]
    for code in codes:
        db_code = session.get(Code, code.code)
        if not db_code:
            session.add(code)
            session.flush()
            session.commit()
            session.refresh(code)
        else:
            has_changes = False
            for attr in ['title', 'poster', 'banner', 'preview_url', 'duration', 'release_date', 'genres', 'casts',
                         'producer', 'publisher',
                         'series', 'still_photo']:
                if hasattr(code, attr) and getattr(code, attr) is not None and getattr(code, attr) != '' and getattr(
                        code, attr) != getattr(db_code, attr):
                    setattr(db_code, attr, getattr(code, attr))
                    has_changes = True

            if has_changes:
                session.flush()
                session.commit()
                session.refresh(db_code)
    filter_actors = []
    is_search_actor = any(query.upper() in actor.name.upper() for actor in actors)
    for actor in actors:
        if is_search_actor:
            if query.upper() in actor.name.upper():
                db_actor = session.get(Actor, actor.name)
                filter_actors.append(db_actor)
        else:
            db_actor = session.get(Actor, actor.name)
            filter_actors.append(db_actor)
    codes = session.query(Code).filter(Code.code.in_(codes_no)).all()
    for code in codes:
        setattr(code, 'is_exist_server', services.is_exist_server(str(code.code)))
    search_result.codes = codes
    search_result.actors = filter_actors
    search_result.torrents = services.sort_torrents(torrents, settings.DEFAULT_SORT.split(','))
    return ResponseEntity(success=True, message='搜索结果', data=search_result.dict())


def manual_download(torrent: Torrent, session: Session) -> ResponseEntity:
    module = get_module()
    settings = get_settings()
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
        if services.download_torrent(torrent_path):
            code_no = find_serial_number(torrent.title)
            if code_no:
                code = session.get(Code, code_no)
                if code:
                    threading.Thread(
                        target=lambda: services.send_complete_message(code.banner, code.code, torrent)).start()
                    code.status = 'COMPLETE'
                    session.commit()
                else:
                    code = services.search_code(code_no)
                    code_banner = ''
                    if code:
                        code_banner = code.banner
                        code.status = 'COMPLETE'
                        session.add(code)
                        session.commit()
                    threading.Thread(
                        target=lambda: services.send_complete_message(code_banner, code_no, torrent)).start()
            else:
                threading.Thread(target=lambda: services.send_complete_message('', '未识别', torrent)).start()
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
            return ResponseEntity(success=True, message='下载成功')

    return ResponseEntity(success=False, message='下载种子失败')


def download_subscribe() -> ResponseEntity:
    threading.Thread(target=lambda: run_codes()).start()
    return ResponseEntity(success=True, message='程序已在后台执行')


def rank_subscribe(codes: str, session: Session) -> ResponseEntity:
    code_arr = codes.split(',')
    code_list = session.query(Code).filter(Code.code.in_(code_arr)).all()
    for code in code_list:
        if code.status == 'UN_SUBSCRIBE' and not services.is_exist_server(code.code):
            settings = get_settings()
            code.filter = json.dumps(settings.DEFAULT_FILTER)
            code.status = 'SUBSCRIBE'
            session.flush()
            session.commit()
            session.refresh(code)
            threading.Thread(target=lambda: services.send_subscribe_message(code.code, code.title, code.banner)).start()
    threading.Thread(target=lambda: run_batch_sub(code_arr)).start()
    return ResponseEntity(success=True, message='订阅完成')


def run_batch_sub(code_no_list: list[str]):
    for code_no in code_no_list:
        run_sub(code_no)
        time.sleep(random.randint(60, 300))


def star_code(code_no: str, session) -> ResponseEntity:
    return None
