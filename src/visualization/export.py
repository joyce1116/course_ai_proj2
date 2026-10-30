"""绘图输入文件的完整性校验。"""

import hashlib
from pathlib import Path


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
