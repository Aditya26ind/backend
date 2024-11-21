from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, User
import os

from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.llms import OpenAI
from app.services.search import search_documents
from app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/queries", tags=["Queries"])

class QueryRequest(BaseModel):
    question: str

@router.post("/query")
async def query_documents(request: QueryRequest, db: Session = Depends(get_db)):
    
    question = request.question
    documents = db.query(Document).all()
   
    print("documents", documents)
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found")


    # Prepare data for LangChain
    texts = [doc.content for doc in documents]
    # ids = [str(doc.id) for doc in documents]

    # Create FAISS vector store
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
    vector_store = FAISS.from_texts(texts, embeddings)

    # Create retrieval chain
    retriever = vector_store.as_retriever()
    qa_chain = RetrievalQA(llm=OpenAI(temperature=0), retriever=retriever)

    answer = qa_chain.run(question)
    return {"answer": answer}



@router.get("/search")
async def search(query: str):
    results = search_documents(query)
    print(results)
    return {"results": results}

@router.get("/search/title")
async def search_by_title(query: str):
    results = search_documents({"match": {"title": query}})
    return {"results": results}

@router.get("/search/user")
async def search_user_documents(query: str, current_user: User = Depends(get_current_user)):
    results = search_documents({"bool": {"must": [{"match": {"content": query}}, {"term": {"user_id": current_user.id}}]}})
    return {"results": results}