from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.sql_generator import (
    SQLGenerator
)
from app.services.sql_validator import (
    SQLValidator
)
from app.services.query_executor import (
    QueryExecutor
)
from app.services.chat_history_service import (
    ChatHistoryService
)
from app.services.chart_service import (
    ChartService
)
from app.services.schema_retriever import (
    SchemaRetriever
)
from app.services.sql_retry_service import (
    SQLRetryService
)

router = APIRouter()


class AskRequest(BaseModel):
    question: str


@router.post("/{session_id}")
def ask_ai(
    session_id: str,
    payload: AskRequest
):

    # Save user message to history
    ChatHistoryService.save_message(
        session_id, "user", payload.question
    )

    try:
        # Generate SQL via RAG
        sql = SQLGenerator.generate(
            session_id, payload.question
        )

        # Validate (only SELECT allowed)
        SQLValidator.validate(sql)

        # Execute query with retry on failure
        try:
            result = QueryExecutor.execute(
                session_id, sql
            )
        except Exception as e:
            # Retry: ask LLM to fix the SQL
            schema = SchemaRetriever.retrieve(
                session_id, payload.question
            )

            corrected = SQLRetryService.fix_sql(
                session_id,
                payload.question,
                schema,
                sql,
                str(e)
            )

            sql = SQLGenerator.clean_sql(corrected)
            SQLValidator.validate(sql)

            result = QueryExecutor.execute(
                session_id, sql
            )

        # Suggest chart visualization
        chart = ChartService.suggest_chart(result)

        # Save assistant response to history
        ChatHistoryService.save_message(
            session_id,
            "assistant",
            f"SQL: {sql}"
        )

        return {
            "question": payload.question,
            "sql": sql,
            "result": result,
            "chart": chart
        }

    except Exception as e:

        # Save error to history
        ChatHistoryService.save_message(
            session_id,
            "assistant",
            f"Error: {str(e)}"
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )