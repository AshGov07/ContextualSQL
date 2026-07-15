import sqlparse
import re

class SQLValidator:

    @staticmethod
    def validate(sql):

        sql = sql.strip()

        # Remove single-line and multi-line comments for reliable parsing
        clean_sql = re.sub(r'--.*', '', sql)
        clean_sql = re.sub(r'/\*.*?\*/', '', clean_sql, flags=re.DOTALL)
        clean_sql = clean_sql.strip()

        if not clean_sql:
            raise Exception(
                "Empty SQL query"
            )

        parsed = sqlparse.parse(clean_sql)

        if not parsed:
            raise Exception(
                "Invalid SQL syntax"
            )

        first_stmt = parsed[0]
        query_type = first_stmt.get_type()

        # Identify the first keyword
        first_token = first_stmt.token_first(skip_cm=True, skip_ws=True)
        first_keyword = str(first_token).upper() if first_token else ""

        # Allow SELECT and CTEs starting with WITH
        if query_type.upper() != "SELECT" and first_keyword not in ("SELECT", "WITH"):
            raise Exception(
                "Only SELECT queries are allowed"
            )

        # Basic sanitization check for destructive actions
        unsafe_keywords = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "CREATE ", "TRUNCATE "]
        for keyword in unsafe_keywords:
            if re.search(r'\b' + re.escape(keyword), clean_sql.upper()):
                raise Exception(
                    f"Destructive operations like {keyword.strip()} are strictly forbidden"
                )

        return True