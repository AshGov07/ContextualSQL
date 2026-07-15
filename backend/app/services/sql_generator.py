import re
from app.services.llm_service import FreeLLM

from app.services.schema_retriever import (
    SchemaRetriever
)


class SQLGenerator:

    @staticmethod
    def get_llm():
        return FreeLLM(
            temperature=0.0
        )

    @staticmethod
    def clean_sql(raw):
        """Extract clean SQL from LLM response
        that may contain markdown code blocks
        or extra explanation text."""

        sql = raw.strip()

        # Remove markdown code blocks like
        # ```sql ... ``` or ``` ... ```
        pattern = r'```(?:sql)?\s*(.*?)\s*```'
        match = re.search(
            pattern, sql, re.DOTALL
        )
        if match:
            sql = match.group(1).strip()

        # Remove leading/trailing quotes
        if (
            sql.startswith('"')
            and sql.endswith('"')
        ):
            sql = sql[1:-1]

        # Remove trailing semicolons
        sql = sql.rstrip(';').strip()

        return sql

    @staticmethod
    def generate(session_id, question):

        schema = SchemaRetriever.retrieve(
            session_id, question
        )

        llm = SQLGenerator.get_llm()

        prompt = f"""
You are an expert Microsoft SQL Server T-SQL developer.

Use only these tables:

{schema}

Important Rules for Lookups & Config Values:
- The table `[ConfigInfoFlat]` is the central repository and absolute source of truth for all lookup values, categories, metadata, and attributes in the entire database. You must always refer to and utilize `[ConfigInfoFlat]` for query context and metadata mapping.
- Columns in other tables like `bloodGroup`, `salutationID`, `sex`, `maritalStatus`, `stateID`, `cityID`, `countryID` contain numeric IDs that link to `ConfigInfoFlat.[configFlatID]`.
- Inside `[ConfigInfoFlat]`, the column `[twig]` represents the category (e.g., 'Salutation', 'State', 'Country', 'City', 'Blood Group', 'Marital Status') and `[itemName]` represents the text name (e.g., 'O+ve', 'Chennai', 'Tamil Nadu', 'Mr.', 'Married').
- **Mapping Query Words to Lookups:** Any text words, names, or values specified in the user's question (such as names of cities, states, blood groups, salutations, or marital status) must be resolved by looking them up in `[ConfigInfoFlat].[itemName]`, matching the corresponding `[twig]` (category), and joining on `[configFlatID]`.
- **Resolving Raw IDs in SELECT:** When retrieving details/records from tables that contain lookup IDs (like `salutationID`, `sex`, `bloodGroup`, `maritalStatus`, `stateID`, `cityID`, `countryID`), do not just return the raw numeric IDs. Perform a `LEFT JOIN` on `[ConfigInfoFlat]` (using separate aliases as needed for each lookup column) to retrieve and select the human-readable text name `[itemName]` under an appropriate alias (e.g., `salutation`, `bloodGroup`, `city`, `state`) instead of or alongside the raw IDs.
- When querying patient records, always select and include `patientID` (and where available, `firstName` and `lastName`) in the SELECT clause so the user can identify the patients.
- **SQL Optimization:** Ensure the generated SQL query is fully optimized. Use proper joins, select only necessary or descriptive columns rather than bloated wildcard SELECTs, avoid unnecessary subqueries, and ensure correct index-friendly joins on primary/foreign keys (e.g., `configFlatID`).

Generate ONLY the T-SQL query.
No explanation. No markdown.
Important: Use T-SQL dialect (e.g., use TOP instead of LIMIT, and square brackets for identifiers).

Question:
{question}
"""

        response = llm.invoke(prompt)

        return SQLGenerator.clean_sql(
            response.content
        )