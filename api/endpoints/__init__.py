
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from app.core.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = get_settings().SECRET_KEY
ALGORITHM = "HS256"


def create_jwt_token(username):
    payload = {
        'username': username
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """从 JWT token 中获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="鉴权没有通过",
        headers={"Authorization": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    return username

