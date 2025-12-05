from pydantic import BaseModel


class Torrent(BaseModel):
    id: int
    site: str
    size_mb: float
    seeders: int
    title: str
    chinese: bool
    uc: bool
    uhd: bool
    free: bool
    download_url: str


