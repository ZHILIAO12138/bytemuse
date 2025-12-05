from typing import Optional, Union

from pydantic import BaseModel


class ResponseEntity(BaseModel):
    # 状态
    success: bool
    # 消息文本
    message: Optional[str] = None
    # 数据
    data: Optional[Union[str, dict, list]] = []

    def __init__(self, success: bool, message: Optional[str] = None, data: Optional[Union[str, dict, list]] = None):
        super().__init__(success=success, message=message, data=data)
        self.success = success
        self.message = message
        if data == []:
            self.data = []
