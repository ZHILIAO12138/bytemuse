import threading
from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import isnot

from app import services
from app.schemas import ActorSubscribe
from app.schemas.reponse import ResponseEntity
from app.database.models import Actor, Cache
from app.modules import get_module





def list(session: Session) -> ResponseEntity:
    actors = session.query(Actor).filter(isnot(Actor.limit_date, None)).all()
    return ResponseEntity(success=True, message="演员列表", data=actors)


def rank(session: Session) -> ResponseEntity:
    module = get_module()
    current_time = datetime.now()
    rank = []
    # 计算8小时前的时间
    time_8_hours_ago = current_time - timedelta(hours=24)
    formatted_time_8_hours_ago = time_8_hours_ago.strftime("%Y-%m-%d %H:%M:%S")
    rank_cache = session.query(Cache).filter(Cache.namespace == 'rank').filter('actors' == Cache.key).filter(
        Cache.create_time >= formatted_time_8_hours_ago).order_by(
        desc(Cache.create_time)).first()
    if rank_cache:
        rank = rank_cache.content.split(',')
    else:
        rank = module.shared.get_shared_rank('actors')
        if not rank:
            rank = module.library.crawling_top20_actor()
        if rank:
            rank_cache = Cache({"namespace": 'rank', "key": "actors", "content": ','.join(rank)})
            session.add(rank_cache)
            session.commit()
    for actor_name in rank:
        db_actor = session.get(Actor, actor_name)
        if not db_actor:
            codes, actors = module.avbase.search_actor(actor_name)
            services.cache_actors(actors, session)
    actors = session.query(Actor).filter(Actor.name.in_(rank)).all()
    session.close()
    sorted_actors = sorted(actors, key=lambda x: rank.index(x.name))
    return ResponseEntity(success=True, message=f'演员榜单', data=sorted_actors)


def subscribe(subscribe: ActorSubscribe, session: Session) -> ResponseEntity:
    actor = session.get(Actor, subscribe.name)
    if actor:
        actor.limit_date = subscribe.limit_date
        session.commit()
    else:
        actor = Actor(subscribe.dict())
        session.add(actor)
        session.commit()
    session.refresh(actor)
    services.subscribe_code_by_actor(actor, session)
    threading.Thread(
        target=lambda: services.send_subscribe_actor_message(actor.name, actor.limit_date, actor.photo)).start()
    session.close()
    return ResponseEntity(success=False, message="订阅成功")


def cancel(actor_name: str, session: Session) -> ResponseEntity:
    actor = session.get(Actor, actor_name)
    if actor:
        session.delete(actor)
        session.commit()
        session.close()
    return ResponseEntity(success=True, message='取消订阅成功')
