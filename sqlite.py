import os
import sqlite3


from typing import (
    Dict,
    List,
    Optional,
    Sequence,
    TypeAlias,
    Union,
)


from logger import log
from zerr import zerr

# Function specific variables and aliases


dbpath = os.getenv("DATABASE_PATH")
SQLiteConn: TypeAlias = sqlite3.Connection


# Functions


def close(connection: SQLiteConn) -> None:
    try:
        connection.close()
    except Exception as e:
        error_info = f"[Failed to close SQLite connection.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        raise Exception(error_info)


def connect(db_path: Optional[str] = None) -> SQLiteConn:
    try:
        if db_path != ":memory:":
            if db_path is None:
                db_path = dbpath

            connection = sqlite3.connect(str(db_path))
        else:
            connection = sqlite3.connect(":memory:")
        return connection
    except Exception as e:
        error_info = f"[Failed to connect to SQLite database.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        raise Exception(error_info)


def create_table(
    connection: SQLiteConn, table_name: str, columns: Dict[str, str]
) -> Optional[bool]:
    try:
        cursor = connection.cursor()
        columns_str = ", ".join(
            f"{key} {value}" for key, value in columns.items()
        )
        query = f"CREATE TABLE {table_name} ({columns_str})"
        cursor.execute(query)
        connection.commit()
        return True
    except Exception as e:
        error_info = f"[Failed to create table {table_name}.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return False


def insert(
    connection: SQLiteConn,
    table_name: str,
    values: Sequence[Union[int, str, bytes, float, None]],
    columns: Optional[Sequence[str]] = None,
) -> Optional[bool]:
    try:
        cursor = connection.cursor()
        placeholders = ", ".join("?" * len(values))
        placeholders = placeholders.replace("\\", "/")
        placeholders = placeholders.replace("'", "`")
        if columns:
            columns_str = ", ".join(columns)
            query = (
                f"INSERT INTO {table_name} "
                f"({columns_str}) VALUES ({placeholders})"
            )
        else:
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"

        cursor.execute(query, values)
        connection.commit()
        return True
    except Exception as e:
        error_info = (
            f"[Failed to insert values into table {table_name}.]:{zerr(e)}"
        )
        log(error_info, "CRITICAL")
        return False


def newdb(db_path: Optional[str] = None) -> Optional[bool]:
    try:
        if db_path is None:
            db_path = dbpath
        connection = connect(db_path)

        create_table(
            connection,
            "media",
            {
                "id": "INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT",
                "filepath": "TEXT NOT NULL UNIQUE",
                "audio": "TEXT",
                "subs": "TEXT",
                "embedded": "TEXT",
                "misc": "TEXT",
                "duplicate": "TEXT",
                "complete": "TEXT",
            },
        )

        close(connection)
        return True

    except Exception as e:
        error_info = f"[Failed to create new SQLite database.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return False


def query(
    connection: SQLiteConn,
    table_name: str,
    columns: Union[str, List[str]] = "*",
    conditions: Optional[
        Dict[str, Union[int, str, bytes, float, None]]
    ] = None,
) -> list:
    try:
        cursor = connection.cursor()
        where_clause = (
            " AND ".join(f"{key} = ?" for key in conditions.keys())
            if conditions
            else ""
        )
        query = (
            f"SELECT {columns} FROM {table_name} "
            f"{'WHERE ' + where_clause if where_clause else ''}"
        )
        cursor.execute(query, list(conditions.values()) if conditions else [])
        return cursor.fetchall()
    except Exception as e:
        error_info = f"[Failed to query table {table_name}.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return []


def raw_query(
    connection: SQLiteConn,
    query: str,
    values: Optional[Dict[str, Union[int, str, bytes, float, None]]] = None,
) -> list:
    try:
        cursor = connection.cursor()
        cursor.execute(query, values if values else [])
        return cursor.fetchall()
    except Exception as e:
        error_info = f"[Failed to execute raw query ({query}).]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return []


def revert_characters(formatted_str: str) -> str:
    subs: Dict[str, str] = {
        "⟦": "[",
        "⟧": "]",
        "⦃": "{",
        "⦄": "}",
        "❨": "(",
        "❩": ")",
        "‚": ",",
        "⁏": ";",
        "❮": "<",
        "❯": ">",
    }
    original_str = formatted_str
    for char, sub in subs.items():
        original_str = original_str.replace(char, sub)
    return original_str


def substitute_characters(original_str: str) -> str:
    subs: Dict[str, str] = {
        "[": "⟦",
        "]": "⟧",
        "{": "⦃",
        "}": "⦄",
        "(": "❨",
        ")": "❩",
        ",": "‚",
        ";": "⁏",
        "<": "❮",
        ">": "❯",
    }
    formatted_str = original_str
    for char, sub in subs.items():
        formatted_str = formatted_str.replace(char, sub)
    return formatted_str


def update(
    connection: SQLiteConn,
    table_name: str,
    values: Dict[str, Union[int, str, bytes, float, None]],
    conditions: Dict[str, Union[int, str, bytes, float, None]],
) -> Optional[bool]:
    try:
        cursor = connection.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in values.keys())
        where_clause = " AND ".join(f"{key} = ?" for key in conditions.keys())
        query = (
            f"UPDATE {table_name} SET {set_clause} " f"WHERE {where_clause}"
        )
        cursor.execute(
            query, list(values.values()) + list(conditions.values())
        )
        connection.commit()
        return True
    except Exception as e:
        error_info = f"[Failed to update table {table_name}.]:{zerr(e)}"
        log(error_info, "CRITICAL")
        return False
