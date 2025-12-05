from typing import List

from app.schemas.torrent import Torrent


def filter_torrents(torrents: List[Torrent], filter: dict):
    filter_list = []
    for torrent in torrents:
        size_mb = torrent.size_mb
        if filter.get('max_size'):
            if size_mb and size_mb > float(filter.get('max_size')):
                continue
        if filter.get('min_size'):
            if size_mb and size_mb < float(filter.get('min_size')):
                continue
        if filter.get('only_chinese'):
            if not torrent.chinese:
                continue
        if filter.get('only_uc'):
            if not torrent.uc:
                continue
        if filter.get('only_uhd'):
            if not torrent.uhd:
                continue
        if filter.get('exclude_uhd'):
            if torrent.uhd:
                continue
        if filter.get('exclude_uc'):
            if torrent.uc:
                continue
        if filter.get('only_free'):
            if not torrent.free:
                continue
        filter_list.append(torrent)
    return filter_list


def sort_torrents(torrents: List[Torrent], sort_by=List[str], main_site=None):
    if not sort_by:
        sort_by = ['seeders']
    sort_by = reversed(sort_by)
    for sort_key in sort_by:
        if sort_key == '!uhd':
            torrents = sorted(torrents, key=lambda torrent: getattr(torrent, "uhd"))
        elif sort_key == '!uc':
            torrents = sorted(torrents, key=lambda torrent: getattr(torrent, "uc"))
        elif sort_key == 'site':
            if main_site:
                torrents = sorted(torrents, key=lambda torrent: torrent.site != main_site)
        else:
            torrents = sorted(torrents, key=lambda torrent: getattr(torrent, sort_key), reverse=True)
    return torrents


cn_keywords: List[str] = ['中字', '中文字幕', '色花堂', '字幕']
uc_keywords: List[str] = ['UC', '无码', '步兵']
uhd_keywords: List[str] = ['4k', '8k', '2160p', '4K', '8K', '2160P']


def has_chinese(title: str):
    has_chinese = False
    for keyword in cn_keywords:
        if title.find(keyword) > -1:
            has_chinese = True
            break
    return has_chinese


def has_uc(title: str):
    uc = False
    for keyword in uc_keywords:
        if title.find(keyword) > -1:
            uc = True
            break
    return uc


def has_uhd(title: str):
    uhd = False
    for keyword in uhd_keywords:
        if title.find(keyword) > -1:
            uhd = True
            break
    return uhd
