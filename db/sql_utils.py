from contextlib import contextmanager
from typing import Any


def fetch_one(connection, query: str, params: tuple | list = ()) -> dict[str, Any]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()


def fetch_all(connection, query: str, params: tuple | list = ()) -> list[dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()


def execute(connection, query: str, params: tuple | list = ()) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        if query.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        return cursor.rowcount
    finally:
        cursor.close()


@contextmanager
def transaction(connection):
    try:
        yield connection
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e


def sql(connection, query: str, params: tuple | list = ()) -> int | dict[str, Any] | list[dict[str, Any]] :
    query_upper = query.strip().upper()

    if query_upper.startswith("SELECT"):
        return fetch_all(connection, query, params)
    else:
        return execute(connection, query, params)