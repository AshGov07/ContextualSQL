import os
import urllib.parse
from sqlalchemy import create_engine

class DatabaseManager:

    _engine = None

    @staticmethod
    def get_engine(session_id=None):
        if DatabaseManager._engine is None:
            server = os.getenv("DB_SERVER", "MLS-AI-PC")
            database = os.getenv("DB_DATABASE", "Mediscan_ObOnly")
            driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
            trust = os.getenv("DB_TRUST_CERTIFICATE", "yes")

            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection={trust};"
                "TrustServerCertificate=yes;"
            )
            params = urllib.parse.quote_plus(conn_str)
            DatabaseManager._engine = create_engine(
                f"mssql+pyodbc:///?odbc_connect={params}",
                pool_pre_ping=True
            )
        return DatabaseManager._engine