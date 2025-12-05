import struct
from urllib.parse import unquote

import requests
from app.modules.cloudnas import clouddrive_pb2
from app.core.config import Settings, get_settings
from app.utils import logger


class CloudNas:
    url: str | None = None
    username: str | None = None
    password: str | None = None
    sava_path: str | None = None

    def __init__(self, settings: Settings):
        self.url = settings.CLOUDNAS_URL
        self.username = settings.CLOUDNAS_USERNAME
        self.password = settings.CLOUDNAS_PASSWORD
        self.sava_path = settings.CLOUDNAS_SAVEPATH

    def get_token(self):
        if self.url and self.username and self.password:
            request = clouddrive_pb2.GetTokenRequest(userName=self.username, password=self.password)
            protobuf_bytes = request.SerializeToString()
            prefix = b'\x00' + struct.pack('>I', len(protobuf_bytes))
            payload = prefix + protobuf_bytes

            headers = {
                "Content-Type": "application/grpc-web",
                "Accept": "*/*",
                "X-User-Agent": "grpc-python/1.0",
                "X-Grpc-Web": "1",  # 关键：告诉服务器你是 grpc-web 客户端
            }
            url = f"{self.url.rstrip()}/clouddrive.CloudDriveFileSrv/GetToken"
            response = requests.post(url, data=payload, headers=headers)
            raw_response = response.content
            if len(raw_response) < 5:
                logger.error("获取token失败")
            else:
                length = int.from_bytes(raw_response[1:5], byteorder="big")
                message_bytes = raw_response[5:5 + length]

                jwt_token = clouddrive_pb2.JWTToken()
                jwt_token.ParseFromString(message_bytes)
                if jwt_token.success:
                    return jwt_token.token
                else:
                    logger.error("获取token失败")
        return None

    def download_offline(self, magnet):
        if self.url and self.username and self.password:
            token = self.get_token()
            if token:
                request = clouddrive_pb2.AddOfflineFileRequest(urls=magnet, toFolder=self.sava_path)
                protobuf_bytes = request.SerializeToString()
                prefix = b'\x00' + struct.pack('>I', len(protobuf_bytes))
                payload = prefix + protobuf_bytes

                headers = {
                    "Content-Type": "application/grpc-web",
                    "Accept": "*/*",
                    "X-User-Agent": "grpc-python/1.0",
                    "X-Grpc-Web": "1",  # 关键：告诉服务器你是 grpc-web 客户端
                    "Authorization": "Bearer " + token,
                }
                url = f"{self.url.rstrip()}/clouddrive.CloudDriveFileSrv/AddOfflineFiles"
                try:
                    response = requests.post(url, data=payload, headers=headers)
                    if response.headers:
                        if response.headers.get("grpc-message"):
                            logger.error(unquote(response.headers.get("grpc-message")))
                    raw_response = response.content
                    if len(raw_response) < 5:
                        logger.error("离线下载失败")
                    else:
                        length = int.from_bytes(raw_response[1:5], byteorder="big")
                        message_bytes = raw_response[5:5 + length]

                        result = clouddrive_pb2.FileOperationResult()
                        result.ParseFromString(message_bytes)
                        if result.success:
                            logger.info("保存成功")
                            return True
                        else:
                            logger.error(result.errorMessage)
                except Exception as e:
                    logger.error(f"云下载失败:{e}")
        return False


if __name__ == '__main__':
    cloudnas = CloudNas(get_settings())
    print(cloudnas.download_offline("magnet:?xt=urn:btih:4B7E2A60E6822F914227F9237B208B5C2E5C9521"))
