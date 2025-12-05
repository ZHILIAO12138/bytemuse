from app.core.config import Settings


class GITHUB:
    proxy: str

    def __init__(self, settings: Settings):
        self.proxy = settings.PROXY

