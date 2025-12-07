import os
import tempfile
from typing import Callable


def atomic_write(path: str, data: bytes, mode: int = 0o600) -> None:
    """Write data to path atomically and set file mode."""
    dirpath = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
        os.chmod(path, mode)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
