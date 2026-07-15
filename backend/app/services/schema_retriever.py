from langchain_chroma import Chroma
from app.services.free_embeddings import FreeEmbeddings
from app.services.schema_service import SchemaService

from app.config import SESSION_DIR


class SchemaRetriever:

    @staticmethod
    def retrieve(
        session_id,
        question
    ):
        # Extract query words
        words = [w.strip("?,.()[]{}'\"").lower() for w in question.lower().split() if w.strip()]

        # 1. Deterministic extraction (Keyword Heuristics)
        all_schemas = SchemaService.get_schema(session_id)
        matched_tables = []

        for table in all_schemas:
            table_name_lower = table['table'].lower()
            
            # Match table name
            table_matched = False
            for w in words:
                if table_name_lower == w or table_name_lower == w.rstrip('s') or w == table_name_lower.rstrip('s'):
                    matched_tables.append(table)
                    table_matched = True
                    break
            if table_matched:
                continue
                
            # Match column name
            for col in table['columns']:
                col_name_lower = col['name'].lower()
                if col_name_lower in words:
                    matched_tables.append(table)
                    break

        embeddings = FreeEmbeddings(session_id)

        db = Chroma(
            persist_directory=str(
                SESSION_DIR
                / session_id
                / "vectordb"
            ),
            embedding_function=embeddings
        )

        docs = []
        try:
            docs = db.similarity_search(
                question,
                k=5
            )
        except Exception as e:
            err_msg = str(e)
            if "dimension" in err_msg or "expecting embedding" in err_msg:
                print(f"[SchemaRetriever] Dimension mismatch detected: {e}. Rebuilding vector store...")
                try:
                    db.delete_collection()
                except Exception as del_err:
                    print(f"[SchemaRetriever] Failed to delete collection: {del_err}")
                
                try:
                    if hasattr(db, "_client") and hasattr(db._client, "close"):
                        db._client.close()
                except Exception as close_err:
                    print(f"[SchemaRetriever] Failed to close client during mismatch handling: {close_err}")
                
                from app.services.schema_embedding_service import SchemaEmbeddingService
                SchemaEmbeddingService.build_vector_store(session_id)
                
                persist_dir = SESSION_DIR / session_id / "vectordb"
                db = Chroma(
                    persist_directory=str(persist_dir),
                    embedding_function=embeddings
                )
                try:
                    docs = db.similarity_search(
                        question,
                        k=5
                    )
                finally:
                    try:
                        if hasattr(db, "_client") and hasattr(db._client, "close"):
                            db._client.close()
                    except:
                        pass
            else:
                try:
                    if hasattr(db, "_client") and hasattr(db._client, "close"):
                        db._client.close()
                except:
                    pass
                raise e
        else:
            try:
                if hasattr(db, "_client") and hasattr(db._client, "close"):
                    db._client.close()
            except Exception as close_err:
                print(f"[SchemaRetriever] Failed to close Chroma client: {close_err}")

        # Combine deterministic matches and semantic search docs
        for doc in docs:
            table_name = None
            for line in doc.page_content.strip().split("\n"):
                if "Table:" in line:
                    table_name = line.replace("Table:", "").strip()
                    break
            if table_name:
                already_added = any(t['table'].lower() == table_name.lower() for t in matched_tables)
                if not already_added:
                    for t in all_schemas:
                        if t['table'].lower() == table_name.lower():
                            matched_tables.append(t)
                            break

        # Ensure [ConfigInfoFlat] is always included in matched_tables
        config_table_added = any(t['table'].lower() == 'configinfoflat' for t in matched_tables)
        if not config_table_added:
            for t in all_schemas:
                if t['table'].lower() == 'configinfoflat':
                    matched_tables.append(t)
                    break

        # Limit total tables in context to prevent token bloat
        matched_tables = matched_tables[:12]

        formatted_docs = []
        for table in matched_tables:
            content = f"Table: {table['table']}\n\nColumns:\n"
            for col in table['columns']:
                content += f"{col['name']} {col['type']}\n"
            formatted_docs.append(content)

        return "\n\n".join(formatted_docs)