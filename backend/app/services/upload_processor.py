import pandas as pd
from pathlib import Path
from sqlalchemy import text

from app.services.database_manager import (
    DatabaseManager
)


class UploadProcessor:

    @staticmethod
    def process_file(
        session_id,
        file_path
    ):

        ext = Path(file_path).suffix.lower()

        if ext in [".xlsx", ".xls"]:
            UploadProcessor.process_excel(
                session_id,
                file_path
            )

        elif ext == ".csv":
            UploadProcessor.process_csv(
                session_id,
                file_path
            )

        elif ext == ".sql":
            UploadProcessor.process_sql(
                session_id,
                file_path
            )

    @staticmethod
    def process_excel(
        session_id,
        file_path
    ):

        engine = DatabaseManager.get_engine(
            session_id
        )

        excel = pd.ExcelFile(file_path)

        for sheet in excel.sheet_names:

            df = pd.read_excel(
                file_path,
                sheet_name=sheet
            )

            table_name = (
                sheet.lower()
                .replace(" ", "_")
            )

            df.to_sql(
                table_name,
                engine,
                if_exists="replace",
                index=False
            )

    @staticmethod
    def process_csv(
        session_id,
        file_path
    ):

        engine = DatabaseManager.get_engine(
            session_id
        )

        table_name = (
            Path(file_path)
            .stem
            .lower()
            .replace(" ", "_")
        )

        df = pd.read_csv(
            file_path
        )

        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False
        )

    @staticmethod
    def process_sql(
        session_id,
        file_path
    ):

        engine = DatabaseManager.get_engine(
            session_id
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            sql_script = f.read()

        with engine.begin() as conn:

            for statement in sql_script.split(";"):

                statement = statement.strip()

                if statement:

                    conn.execute(
                        text(statement)
                    )