import pandas as pd
import numpy as np

from app.services.database_manager import (
    DatabaseManager
)


class QueryExecutor:

    @staticmethod
    def execute(session_id, sql):

        engine = DatabaseManager.get_engine(
            session_id
        )

        df = pd.read_sql(sql, engine)

        # Convert NaN, NaT, Infinity to None
        df = df.replace(
            [np.nan, np.inf, -np.inf],
            None
        )

        total_rows = len(df)

        return {
            "columns": df.columns.tolist(),
            "rows": df.to_dict(
                orient="records"
            ),
            "total_rows": total_rows
        }