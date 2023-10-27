import os
import sys


from pathlib import Path
from typing import Optional


asset_folder_name = "assets"  # change to desired asset folder name
force_debug_mode = False  # change to True to force debug mode
log_folder_name = ".logs"  # change to desired log folder name
scratch_dir = "./scratch"  # change to desired scratch folder name

os.environ["ASSET_DIR"] = asset_folder_name if asset_folder_name else "assets"
os.environ["LOG_DIR"] = log_folder_name if log_folder_name else ".logs"
os.environ["LOCAL_TEMP"] = scratch_dir if scratch_dir else "./scratch"

current_path = Path(__file__).resolve()
parent_path = current_path.parent

sys.path.append(str(parent_path))


def db_check() -> Optional[str]:
    from logger import log
    from sqlite import connect, close, newdb
    from utils import find_newest_file_in_dir as lookup_file, get_system_id
    from zerr import zerr

    try:
        db_dir = os.path.join(parent_path, os.environ["ASSET_DIR"])
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = lookup_file(db_dir, ".db")
        if db_path is None:
            new_db_name = f"{get_system_id()}.db"
            new_db_path = os.path.join(db_dir, new_db_name)
            newdb(new_db_path)
            return new_db_path
        else:
            test = connect(db_path)
            if test is not None:
                close(test)
                return db_path
            else:
                raise Exception(
                    f"Found database {db_path} but failed to connect."
                )
    except Exception as e:
        error_info = f"[Database Check Failed]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return None


if __name__ == "__main__":
    import argparse

    os.environ["DB_PATH"] = str(db_check())

    parser = argparse.ArgumentParser(
        description="Check audio and subtitle tracks in a video file."
    )
    parser.add_argument(
        "-f", "--filepath", type=str, help="Path to the video file."
    )
    parser.add_argument(
        "-s",
        "--search",
        type=int,
        help="Boolean for searching or not. Use 0 for False, 1 for True.",
        default=0,
    )
    parser.add_argument(
        "-r",
        "--reconcile",
        type=int,
        help="Boolean for reconciling or not. Use 0 for False, 1 for True.",
        default=0,
    )

    args = parser.parse_args()

    if args.reconcile == 1:
        from app import reconcile

        reconcile()
    elif args.search == 1:
        from app import search

        top_level_folder = args.filepath

        if top_level_folder is None:
            top_level_folder = os.getcwd()

        search(top_level_folder)
    else:
        if args.filepath is None:
            from logger import log
            from zerr import zerr

            error_info = zerr(
                Exception(
                    "No filepath arg provided. Please provide a filepath."
                )
            )
            log(error_info, "CRITICAL")
        else:
            from app import check_audio_subtitle

            normalized_absolute_path = (
                os.path.abspath(args.filepath)
            ).replace("\\", "/")
            normalized_absolute_path = normalized_absolute_path.replace(
                "'", "`"
            )
            result = check_audio_subtitle(normalized_absolute_path)

            if "error" in result:
                raise Exception(result["error"])
            else:
                from sqlite import connect
                from app import update

                connection = connect(os.environ["DB_PATH"])
                if connection is None:
                    raise Exception("Failed to connect to database.")
                update(
                    connection,
                    "media",
                    {"complete": "True"},
                    {"id": str(result["id"])},
                )
