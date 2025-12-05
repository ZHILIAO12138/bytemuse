from fastapi import APIRouter

from app.api.services import ipicproxy

router = APIRouter()


@router.get("/image-proxy")
def image_proxy(url: str):
    return ipicproxy.image_proxy(url)
