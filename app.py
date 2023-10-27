import os


from pydub.utils import mediainfo
from pymkv import MKVFile
from typing import Optional, Union, List, Dict


from logger import log
from sqlite import connect, insert, raw_query, SQLiteConn
from zerr import zerr


def check_audio_subtitle(
    file_path: str,
) -> Dict[str, Union[int, List[str], str]]:
    connection = None
    og_filepath = os.path.abspath(file_path)
    og_filepath = og_filepath.replace("/", "\\")
    og_filepath = og_filepath.replace("`", "'")
    filepath = og_filepath.replace("\\", "/")
    filepath = filepath.replace("'", "`")
    try:
        connection = connect(os.environ["DB_PATH"])
    except Exception as e:
        error_info = f"[Failed to connect to database for check]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return {"error": error_info}
    if connection is None:
        error_info = (
            "[Failed to connect to database for check]:Connection is None"
        )
        log(error_info, "CRITICAL")
        return {"error": error_info}
    try:
        existing_records = raw_query(
            connection,
            "SELECT id, complete FROM " f"media where filepath = '{filepath}'",
        )

        if not existing_records:
            insert(
                connection,
                "media",
                [None, filepath, None, None, None, None, None, None],
            )
            existing_records = raw_query(
                connection,
                "SELECT id, complete FROM "
                f"media where filepath = '{filepath}'",
            )
        if existing_records[0][1] == "True":
            return {}

        result = {
            "id": existing_records[0][0],
            "audio": [],
            "subtitles": [],
        }

        if og_filepath.endswith(".mkv"):
            mkv = MKVFile(og_filepath)

            audio_tracks = [
                track for track in mkv.tracks if track.track_type == "audio"
            ]
            for track in audio_tracks:
                if not result["audio"] is None or len(result["audio"]) > 0:
                    result["audio"].append(track.language)

                subtitle_tracks = [
                    track
                    for track in mkv.tracks
                    if track.track_type == "subtitles"
                ]
                for track in subtitle_tracks:
                    if (
                        not result["subtitles"] is None
                        or len(result["subtitles"]) > 0
                    ):
                        result["subtitles"].append(track.language)
            if (
                "eng" in result["subtitles"]
                and len(result["audio"]) > 0
                and len(result["subtitles"]) > 0
            ):
                update(
                    connection,
                    "media",
                    {"complete": "True", "embedded": "True"},
                    {"id": result["id"]},
                )

        elif og_filepath.endswith(".mp4") or og_filepath.endswith(".avi"):
            info = mediainfo(og_filepath)

            if "streams" not in info:
                streams = [info]
            else:
                streams = info["streams"]

            for stream in streams:
                if stream.get("codec_type") == "audio":
                    result["audio"].append(stream.get("language", "unknown"))

            for stream in streams:
                if stream.get("codec_type") == "subtitle":
                    result["subtitles"].append(
                        stream.get("language", "unknown")
                    )

            if len(result["audio"]) > 0 and len(result["subtitles"]) > 0:
                update(
                    connection,
                    "media",
                    {"embedded": "True"},
                    {"id": result["id"]},
                )

            check_srt(og_filepath, filepath, connection, result)

        else:
            raise Exception(f"Unsupported file type: {og_filepath}")

        if len(result["audio"]) > 0:
            update(
                connection,
                "media",
                {"audio": ",".join(result["audio"])},
                {"id": result["id"]},
            )

        if len(result["subtitles"]) > 0:
            for subtitle in result["subtitles"]:
                if subtitle == ".en" or subtitle == ".eng":
                    result["subtitles"].add("eng")
                elif subtitle == "unknown":
                    result["subtitles"].remove("unknown")
            update(
                connection,
                "media",
                {"subs": ",".join(result["subtitles"])},
                {"id": result["id"]},
            )

        check_for_duplicate(og_filepath)

        return result
    except Exception as e:
        error_info = f"[Failed to check audio and subtitle tracks]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return {"error": error_info}


def check_for_duplicate(file_path: str) -> Optional[bool]:
    og_filepath = os.path.abspath(file_path)
    og_filepath = og_filepath.replace("/", "\\")
    og_filepath = og_filepath.replace("`", "'")
    filepath = og_filepath.replace("\\", "/")
    filepath = filepath.replace("'", "`")
    connection = None
    try:
        connection = connect(os.environ["DB_PATH"])
    except Exception as e:
        error_info = f"[Failed to connect to database for check]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return
    if connection is None:
        error_info = (
            "[Failed to connect to database for check]:Connection is None"
        )
        log(error_info, "CRITICAL")
        return
    try:
        basename_with_ext = os.path.basename(og_filepath)
        basename_no_ext = os.path.splitext(basename_with_ext)[0]
        converted_basename_no_ext = basename_no_ext.replace("'", "`")
        converted_basename_no_ext = converted_basename_no_ext.replace(
            "\\", "/"
        )
        existing_records = raw_query(
            connection,
            f"SELECT id FROM media WHERE filepath LIKE "
            f"'%{converted_basename_no_ext}%' "
            f"AND filepath NOT LIKE '{filepath}'",
        )
        records = []
        for record in existing_records:
            record_filepath = raw_query(
                connection,
                f"SELECT filepath FROM media WHERE id = {record[0]}",
            )
            if not record_filepath[0][0].endswith(".srt"):
                records.append(record_filepath[0][0])
            else:
                continue

        if len(records) > 0:
            update(
                connection,
                "media",
                {"duplicate": ",".join(records)},
                {"filepath": filepath},
            )
            return True
        else:
            return False
    except Exception as e:
        error_info = f"[Failed to check for duplicate]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return


def reconcile():
    connection = None
    try:
        connection = connect(os.environ["DB_PATH"])
    except Exception as e:
        error_info = f"[Failed to connect to database for reconcile]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return
    if connection is None:
        error_info = (
            "[Failed to connect to database for reconcile]:Connection is None"
        )
        log(error_info, "CRITICAL")
        return
    try:
        records = raw_query(
            connection,
            "SELECT id, filepath FROM media WHERE id IS NOT NULL "
            "AND filepath IS NOT NULL AND complete IS NOT 'True'",
        )
        for record in records:
            og_filepath = os.path.abspath(record[1])
            filepath = og_filepath.replace("\\", "/")
            filepath = filepath.replace("'", "`")
            check_result = check_audio_subtitle(filepath)
            if "error" in check_result:
                continue
            if "id" in check_result and "embedded" in check_result == "True":
                update(
                    connection,
                    "media",
                    {"complete": "True"},
                    {"id": str(check_result["id"])},
                )
    except Exception as e:
        error_info = (
            f"[Failed to reconcile audio and subtitle tracks]:{zerr(e)}"
        )
        log(error_info, "CRITICAL")
        return


def search(top_level_folder: str):
    connection = None
    try:
        connection = connect(os.environ["DB_PATH"])
    except Exception as e:
        error_info = f"[Failed to connect to database for search]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return
    if connection is None:
        error_info = (
            "[Failed to connect to database for search]:Connection is None"
        )
        log(error_info, "CRITICAL")
        return
    for root, _, files in os.walk(top_level_folder):
        for file in files:
            try:
                if file.endswith((".mp4", ".mkv", ".avi")):
                    og_filepath = os.path.abspath(os.path.join(root, file))
                    og_filepath = og_filepath.replace("/", "\\")
                    og_filepath = og_filepath.replace("`", "'")
                    filepath = og_filepath.replace("\\", "/")
                    filepath = filepath.replace("'", "`")
                    existing_records = raw_query(
                        connection,
                        f"SELECT id FROM media WHERE filepath = '{filepath}'",
                    )
                    if existing_records:
                        continue
                    insert(
                        connection,
                        "media",
                        [None, filepath, None, None, None, None, None, None],
                    )
                elif file.endswith(".srt"):
                    og_filepath = os.path.abspath(os.path.join(root, file))
                    og_filepath = og_filepath.replace("/", "\\")
                    og_filepath = og_filepath.replace("`", "'")
                    filepath = og_filepath.replace("\\", "/")
                    filepath = filepath.replace("'", "`")

                    media_name, lang_code = (
                        file.rsplit(".", 2)[0],
                        file.rsplit(".", 2)[1],
                    )
                    if lang_code == ".en" or ".eng":
                        lang_code = "eng"
                    existing_records = raw_query(
                        connection,
                        "SELECT id FROM media WHERE filepath = "
                        f"'{media_name}.mkv'",
                    )
                    if existing_records:
                        update(
                            connection,
                            "media",
                            {"misc": f"{media_name}.{lang_code}.srt"},
                            conditions={"filepath": f"{media_name}.mkv"},
                        )
            except Exception as e:
                error_info = f"[Failed to search for media files]:{zerr(e)}"
                log(error_info, "CRITICAL")
                continue


def check_srt(
    og_filepath: str, filepath: str, connection: SQLiteConn, result
) -> Optional[bool]:
    dirname = os.path.dirname(og_filepath)
    basename_no_ext = os.path.splitext(os.path.basename(og_filepath))[0]

    for potential_srt in os.listdir(dirname):
        if potential_srt.startswith(
            basename_no_ext
        ) and potential_srt.endswith(".srt"):
            lang_code = ""
            if potential_srt.count(".") == 2:
                lang_code = "." + potential_srt.rsplit(".", 2)[1]
            result["subtitles"].append(lang_code)
            converted_basename_no_ext = basename_no_ext.replace("'", "`")
            converted_basename_no_ext = converted_basename_no_ext.replace(
                "\\", "/"
            )
            misc_cache = raw_query(
                connection,
                f"SELECT misc FROM media WHERE id = {result['id']}",
            )
            srt_name = f"{converted_basename_no_ext}{lang_code}.srt"
            misccache = misc_cache[0][0]
            if misccache is None:
                misc_result = srt_name
            elif srt_name in misccache:
                misc_result = misccache
            else:
                misc_result = misccache + "," + srt_name
            update(
                connection,
                "media",
                {
                    "misc": misc_result,
                },
                {"id": result["id"]},
            )


def update(
    connection: SQLiteConn,
    table_name: str,
    values: Dict[str, Union[int, str, bytes, float, None]],
    conditions: Dict[str, Union[int, str, bytes, float, None]],
) -> Optional[bool]:
    try:
        cursor = connection.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in values.keys())
        set_clause.replace("\\", "/")
        set_clause.replace("'", "`")
        where_clause = " AND ".join(f"{key} = ?" for key in conditions.keys())
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        cursor.execute(
            query, list(values.values()) + list(conditions.values())
        )
        connection.commit()
        return True
    except Exception as e:
        error_info = f"[Update Failed]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return False
