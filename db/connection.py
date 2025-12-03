from typing import Generator
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

from config import DB_DATABASE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=False
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise


def close_db_connection(connection):
    if connection and connection.is_connected():
        connection.close()


@contextmanager
def get_db():
    connection = get_db_connection()
    try:
        yield connection
    finally:
        close_db_connection(connection)


def get_db_dependency() -> Generator:
    connection = get_db_connection()
    try:
        yield connection
    finally:
        close_db_connection(connection)