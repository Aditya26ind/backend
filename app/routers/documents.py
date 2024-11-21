import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.services.awss3 import upload_to_s3
from app.database import get_db
from app.models import Document, User
from app.services.search import index_document
from app.routers.auth import get_current_user
import json
from PyPDF2 import PdfReader
import traceback

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        filename=file.filename
        # Read the file content and create a copy for post-upload processing
        file_bytes = await file.read()  # Read file content
        file_copy = io.BytesIO(file_bytes)  # Create an in-memory copy for PDF parsing

        # Upload to S3
        file_copy_for_s3 = io.BytesIO(file_bytes)  # Another copy for S3 upload
        file_url = await upload_to_s3(file_copy_for_s3,filename)

        # Reset file pointer for PDF parsing
        file_copy.seek(0)

        # Parse the PDF content
        if file.content_type == "application/pdf":
            pdf_reader = PdfReader(file_copy)
            text_content = "\n".join(page.extract_text() or '' for page in pdf_reader.pages)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Save metadata and content in the database
        
        print(file)
        document = Document(
            title=filename,
            content=text_content,
            metadata=json.dumps({"file_url": file_url}),
            user_id=current_user.id,  # Replace with actual user ID from authentication
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Index the document for search functionality
        index_document(document.id, document.title, document.content)

        return {"message": "Document uploaded and parsed successfully", "id": document.id}
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error during document upload: {e}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail="An error occurred during document upload.")

@router.get("/{id}")
def get_document(id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    try:
        document = db.query(Document).filter(Document.id == id, Document.user_id == current_user.id).first()
        print(document)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"id": document.id, "title": document.title, "content": document.content}
    except Exception as e:
        print(f"Error fetching document: {e}")
        return {"error": str(e)}

@router.delete("/{id}")
def delete_document(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(document)
    db.commit()
    return {"message": "Document deleted successfully"}

@router.get("/metadata")
def filter_documents(metadata_key: str, metadata_value: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    filtered = [
        doc for doc in documents 
        if metadata_key in doc.metaDatas and doc.metaDatas[metadata_key] == metadata_value
    ]
    return {"filtered_documents": filtered}