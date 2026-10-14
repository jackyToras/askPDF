from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import traceback

from utils import (
    process_and_embed,
    save_to_chromadb,
    answer_query,
    get_chroma_client,
    get_supported_formats
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

client = get_chroma_client()
COLLECTION_NAME = "documents"


class Question(BaseModel):
    question: str


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/supported-formats")
def supported_formats():
    return {"formats": get_supported_formats()}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = "default"):
    ext = os.path.splitext(file.filename)[-1].lower().replace(".", "")
    if ext not in get_supported_formats():
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks = process_and_embed(file_path, user_id=user_id, filename=file.filename)
        if not chunks:
            raise HTTPException(status_code=400, detail="No extractable content found in document")

        save_to_chromadb(chunks, client, COLLECTION_NAME)

        return {
            "filename": file.filename,
            "total_chunks": len(chunks),
            "user_id": user_id,
            "message": "Document uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/query")
def query(request: Question, user_id: str = "default"):
    """
    Query documents for a specific user.
    User isolation: only this user's documents are searched.
    """
    answer = answer_query(
        request.question,
        client,
        COLLECTION_NAME,
        user_id=user_id
    )
    return {
        "answer": answer,
        "user_id": user_id
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)