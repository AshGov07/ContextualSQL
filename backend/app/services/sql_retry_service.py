from app.services.sql_generator import SQLGenerator
from app.services.conversation_memory import (
    ConversationMemory
)

class SQLRetryService:

    @staticmethod
    def fix_sql(
        session_id,
        question,
        schema,
        bad_sql,
        error_message
    ):
        memory = (
            ConversationMemory
            .get_context(session_id)
        )

        prompt = f"""
You generated invalid Microsoft SQL Server T-SQL.

Conversation Memory:
{memory}

Question:
{question}

Schema:
{schema}

Generated SQL:
{bad_sql}

SQL Server Error:
{error_message}

Generate corrected T-SQL only.
"""

        llm = SQLGenerator.get_llm()

        response = llm.invoke(prompt)

        return response.content