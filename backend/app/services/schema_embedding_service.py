from langchain_core.documents import Document
from langchain_chroma import Chroma
from app.services.free_embeddings import FreeEmbeddings

from app.services.schema_service import SchemaService
from app.config import SESSION_DIR


class SchemaEmbeddingService:

    @staticmethod
    def build_vector_store(session_id, offset: int = 0, limit: int = 50, temp_gemini_key: str = None, force_provider: str = None):

        schema = SchemaService.get_schema(
            session_id
        )

        sliced_schema = schema[offset:offset+limit]

        docs = []

        for table in sliced_schema:

            content = f"""
            Table: {table['table']}

            Columns:
            """

            for col in table["columns"]:

                content += (
                    f"{col['name']} "
                    f"{col['type']}\n"
                )

            docs.append(
                Document(
                    page_content=content
                )
            )

        embeddings = FreeEmbeddings(session_id, temp_gemini_key=temp_gemini_key, force_provider=force_provider)

        persist_dir = (
            SESSION_DIR
            / session_id
            / "vectordb"
        )

        import shutil
        if offset == 0:
            # 1. Take a backup of the old database if it exists
            if persist_dir.exists():
                backup_dir = SESSION_DIR / session_id / "vectordb_backup"
                if backup_dir.exists():
                    try:
                        shutil.rmtree(backup_dir)
                    except:
                        pass
                try:
                    shutil.copytree(persist_dir, backup_dir)
                    print(f"[SchemaEmbeddingService] Backed up old vectordb to {backup_dir}")
                except Exception as backup_err:
                    print(f"[SchemaEmbeddingService] Warning: failed to backup vectordb: {backup_err}")
            
            # 2. Clear old cached provider
            cached_file = SESSION_DIR / session_id / "active_embedding_provider.txt"
            if cached_file.exists():
                try:
                    cached_file.unlink()
                except Exception as unlink_err:
                    print(f"[SchemaEmbeddingService] Warning: failed to delete provider cache: {unlink_err}")

            # 3. Clean start - remove the old vectordb
            if persist_dir.exists():
                try:
                    shutil.rmtree(persist_dir)
                except Exception as e:
                    print(f"[SchemaEmbeddingService] Warning: failed to delete old vectordb: {e}")

        # If docs is empty, return progress report
        if not docs:
            return {"processed": 0, "total": len(schema), "offset": offset}

        # Build / append Chroma database
        if offset == 0:
            db = Chroma.from_documents(
                docs,
                embeddings,
                persist_directory=str(
                    persist_dir
                )
            )
        else:
            db = Chroma(
                persist_directory=str(persist_dir),
                embedding_function=embeddings
            )
            db.add_documents(docs)
        
        try:
            if hasattr(db, "_client") and hasattr(db._client, "close"):
                db._client.close()
        except Exception as close_err:
            print(f"[SchemaEmbeddingService] Warning: failed to close Chroma client: {close_err}")

        return {"processed": len(docs), "total": len(schema), "offset": offset}