import glob
import hashlib
import os
import platform


from typing import Optional


from logger import log
from zerr import zerr


def find_newest_file_in_dir(directory: str, extension: str) -> Optional[str]:
    try:
        files = glob.glob(f"{directory}/*{extension}")
        if not files:
            return None
        newest_file = max(files, key=os.path.getmtime)
        return newest_file
    except Exception as e:
        error_info = f"[Failed to find newest file in directory.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return None


def get_system_id() -> Optional[str]:
    try:
        sys_info = platform.uname()
        unique_str = (
            f"{sys_info.system}{sys_info.node}{sys_info.release}"
            f"{sys_info.version}{sys_info.machine}{sys_info.processor}"
        )
        hash_object = hashlib.sha256(unique_str.encode())
        hash_hex = hash_object.hexdigest()
        return hash_hex[:8]
    except Exception as e:
        error_info = f"[Failed to generate system ID.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return None
