from app.modules.cloudnas.cloudnas import CloudNas
from app.modules.dockerhub.dockerhub import DockerHub
from app.modules.downloadclient.qbittorrent import QBitTorrentClient
from app.modules.downloadclient.transmission import TransmissionClient
from app.modules.downloadclient.thunder import Thunder
from app.modules.github.github import GITHUB
from app.modules.ladysite.avbase import AVBase
from app.modules.ladysite.javdb import Avdb
from app.modules.mediaserver.emby import Emby
from app.modules.mediaserver.jellyfin import Jellyfin
from app.modules.mediaserver.plex import Plex
from app.modules.mongo.shared import Shared
from app.modules.notify.telegram import TelegramNotifier
from app.modules.notify.wechat import WeChatNotifier
from app.modules.ladysite.bus import Bus
from app.modules.ladysite.library import Library
from app.modules.ladysite.jable import Jable
from app.modules.ladysite.brands import Brands
from app.modules.ptsite.mteam import MTeam
from app.modules.ptsite.nicept import NicePT
from app.modules.ptsite.ptt import PTT
from app.modules.ptsite.rousi import Rousi
from app.modules.mongo.sehuatang import SeHuaTang
from app.core.config import get_settings


class Module:
    emby: Emby = None
    plex: Plex = None
    jellyfin: Jellyfin = None
    library: Library = None
    avdb: Avdb = None
    avbase: AVBase = None
    bus: Bus = None
    jable: Jable = None
    nicept: NicePT = None
    rousi: Rousi = None
    ptt: PTT = None
    mteam: MTeam = None
    qbittorrent: QBitTorrentClient = None
    transmission: TransmissionClient = None
    thunder: Thunder = None
    wechat: WeChatNotifier = None
    telegram: TelegramNotifier = None
    dockerhub: DockerHub = None
    github: GITHUB = None
    sht: SeHuaTang = None
    cloud_nas: CloudNas = None
    shared: Shared = None
    brands: Brands = None

    def __init__(self):
        settings = get_settings()
        self.emby = Emby(settings)
        self.plex = Plex(settings)
        self.jellyfin = Jellyfin(settings)
        self.library = Library(settings)
        self.avdb = Avdb(settings)
        self.avbase = AVBase(settings)
        self.bus = Bus(settings)
        self.jable = Jable(settings)
        self.mteam = MTeam(settings)
        self.nicept = NicePT(settings)
        self.ptt = PTT(settings)
        self.rousi = Rousi(settings)
        self.sht = SeHuaTang(settings)
        self.qbittorrent = QBitTorrentClient(settings)
        self.transmission = TransmissionClient(settings)
        self.thunder = Thunder(settings)
        self.wechat = WeChatNotifier(settings)
        self.telegram = TelegramNotifier(settings)
        self.dockerhub = DockerHub(settings)
        self.github = GITHUB(settings)
        self.cloud_nas = CloudNas(settings)
        self.shared = Shared()
        self.brands = Brands(settings)
        pass


_module = None


def load_module():
    global _module
    _module = Module()
    return _module


def get_module():
    global _module
    if _module is None:
        return load_module()
    return _module


load_module()
