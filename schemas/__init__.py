from typing import List

from pydantic import BaseModel


class ActorSubscribe(BaseModel):
    name: str
    photo: str | None
    limit_date: str


class CodeSubscribe(BaseModel):
    code: str
    filter: dict
    mode: str


class CodeQuery(BaseModel):
    page: int
    size: int
    query: str
    status: str


class SearchResult(BaseModel):
    codes: List[dict] | None
    actors: List[dict] | None
    torrents: List[dict] | None


class Dashboard(BaseModel):
    sub_count: int | None
    actor_count: int | None
    complete_count: int | None
    most_actor: dict | None
    most_series: dict | None
    most_publisher: dict | None
    release_today: List[dict] | None
    actor_photo: str | None