from fastapi import APIRouter, Depends

from app.api.endpoints import get_current_user
from app.api.services import iconfig
from app.schemas.reponse import ResponseEntity
from app.core.config import Settings
from app.version import AL_VERSION
from app.modules import get_module
from app.utils.log import logger

router = APIRouter()


@router.get("/config")
def get_config(current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return iconfig.get_config()


@router.post("/config")
async def save_config(config: Settings, current_user: str = Depends(get_current_user)) -> ResponseEntity:
    return iconfig.save_config(config)


@router.get("/version")
def get_version(current_user: str = Depends(get_current_user)) -> ResponseEntity:
    latest_version, changes = iconfig.get_latest_version()
    version = {
        "version": AL_VERSION,
        "latest_version": latest_version if latest_version else AL_VERSION,
        "changes": changes
    }
    return ResponseEntity(success=True, message="", data=version)



@router.get("/logs")
def get_logs(lines: int = 100, current_user: str = Depends(get_current_user)) -> ResponseEntity:
    logs = iconfig.get_logs(lines)
    return ResponseEntity(success=True, message="", data=logs)


@router.get("/status")
def get_status(site: str = None, current_user: str = Depends(get_current_user)) -> ResponseEntity:
    module = get_module()
    status = None
    if site == "mteam":
        status = module.mteam.check_status()
    elif site == "bypass":
        status = iconfig.get_bypass_status()
    logger.info(f"站点{site}状态: {status}")
    return ResponseEntity(success=True, message="", data={"status": status})


@router.get("/healthy")
def healthy_check(module_name: str = None, current_user: str = Depends(get_current_user)) -> ResponseEntity:
    module = get_module()
    health, duration = module.__getattribute__(module_name).healthy_check()
    health.time_cost = int(duration)
    return ResponseEntity(success=True, message="", data=health.to_dict())
