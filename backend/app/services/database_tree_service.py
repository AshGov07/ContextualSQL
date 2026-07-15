from sqlalchemy import inspect, text

from app.services.database_manager import (
    DatabaseManager
)


class DatabaseTreeService:

    @staticmethod
    def get_tree(session_id):

        engine = (
            DatabaseManager.get_engine(
                session_id
            )
        )

        inspector = inspect(engine)

        result = []

        for table in inspector.get_table_names():
            # Filter out system and internal tables
            if table.lower().startswith(("sys", "dtproperties", "spt_")) or "conflict" in table.lower() or "trace" in table.lower():
                continue

            columns = inspector.get_columns(
                table
            )

            count = 0
            try:
                with engine.connect() as conn:
                    # Use brackets for SQL Server compatibility
                    count = conn.execute(
                        text(
                            f"SELECT COUNT(*) FROM [{table}]"
                        )
                    ).scalar()
            except Exception as e:
                print(f"[DatabaseTreeService] Warning: count failed for {table}: {e}")

            result.append({
                "table": table,
                "row_count": count,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(
                            col["type"]
                        )
                    }
                    for col in columns
                ]
            })

        return result