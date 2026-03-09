from __future__ import annotations

import platform
import socket

import psutil
from orion.utils.schema import BaseModel

from orion.tools.base import BaseTool


class GetSystemInfoArgs(BaseModel):
    pass


class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    description = "Return CPU, RAM, platform and local IP details."
    args_schema = GetSystemInfoArgs

    def execute(self, **kwargs) -> str:
        _ = self.args_schema(**kwargs)
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        ip = socket.gethostbyname(socket.gethostname())
        return (
            f"platform={platform.platform()}\n"
            f"cpu_percent={cpu}\n"
            f"ram_percent={mem.percent}\n"
            f"ram_used_gb={round(mem.used / (1024**3), 2)}\n"
            f"ip={ip}"
        )
