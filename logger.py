import os
import re

from datetime import datetime
from icecream import ic
from typing import Optional


def get_log_path() -> str:
    log_dir = os.path.join(os.getcwd(), os.getenv("LOG_DIR", ".logs"))
    today = str(fix_datetime(datetime.utcnow())).split(" ")[0]
    time_stamp = re.sub(r"\W+", "", str(today))

    if os.path.exists(log_dir) and not os.path.isdir(log_dir):
        raise Exception(f"[{log_dir}] already exists as a file.")

    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            raise Exception(f"Failed to create log directory at [{log_dir}]")

    return os.path.join(log_dir, f"{time_stamp}.log")


def log(
    log_message: str,
    level: str = "INFO",
    success: bool = False,
    console: bool = False,
) -> None:
    console = True if os.environ.get("FORCE_DEBUG") == "True" else console
    today = str(fix_datetime(datetime.utcnow())).split(" ")[0]
    now = fix_datetime(datetime.utcnow(), milliseconds=True)

    if console:
        ic(f"[{now}] {level}: {log_message}")

    try:
        log_file = get_log_path()
        is_new_file = not os.path.exists(log_file)

        with open(log_file, "a") as f:
            if is_new_file:
                f.write(f"[{now}] ***START_OF_LOG for {today}***.\n")
            if success:
                f.write(f"[{now}] [INFO] Success: {log_message}\n")
            else:
                f.write(f"[{now}] [{level}] Error: {log_message}\n")
    except Exception as e:
        ic(f"[{now}] [{level}] Error: {log_message} | Exception: {e}")


def fix_datetime(
    input_time: datetime, milliseconds: bool = False
) -> Optional[str]:
    try:
        if isinstance(input_time, (int, float)):
            input_time = datetime.fromtimestamp(input_time / 1000)
        else:
            input_time = datetime.strptime(
                str(input_time), "%Y-%m-%d %H:%M:%S.%f"
            )
        if milliseconds:
            return input_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        else:
            return input_time.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError) as e:
        raise Exception(f"Failed to format datetime: {e}")
