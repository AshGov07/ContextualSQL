from sqlalchemy import inspect

from app.services.database_manager import (
    DatabaseManager
)


class SchemaService:

    @staticmethod
    def get_schema(
        session_id
    ):

        engine = DatabaseManager.get_engine(
            session_id
        )

        inspector = inspect(engine)

        result = []

        for table in inspector.get_table_names():
            # Filter out system and internal tables
            if table.lower().startswith(("sys", "dtproperties", "spt_")) or "trace" in table.lower():
                continue

            columns = []

            for column in inspector.get_columns(
                table
            ):

                columns.append({
                    "name": column["name"],
                    "type": str(
                        column["type"]
                    )
                })

            result.append({
                "table": table,
                "columns": columns
            })

        return result