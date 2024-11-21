from elasticsearch import Elasticsearch
import os

# Initialize Elasticsearch client
es = Elasticsearch(
    "https://my-elasticsearch-project-a5143b.es.us-east-1.aws.elastic.cloud:443",
    api_key=os.getenv("ELASTIC_SEARCH_API_KEY")
)

INDEX_NAME = "documents"

# Ensure the index exists
def create_index():
    try:
        if not es.indices.exists(index=INDEX_NAME):
            mappings = {
                "mappings": {
                    "properties": {
                        "id": {"type": "text"},
                        "title": {"type": "text"},
                        "content": {"type": "text"}
                    }
                }
            }
            response = es.indices.create(index=INDEX_NAME, body=mappings)
            print(f"Index created successfully: {response}")
        else:
            print(f"Index '{INDEX_NAME}' already exists.")
    except Exception as e:
        print(f"Error creating index: {e}")
        raise

# Insert one document at a time
def index_document(doc_id, title, content):
    try:
        doc = {
            "id": doc_id,
            "title": title,
            "content": content
        }
        response = es.index(index=INDEX_NAME, id=doc_id, document=doc)
        print(f"Document indexed successfully: {response}")
    except Exception as e:
        print(f"Error indexing document: {e}")
        raise

# Search documents
def search_documents(query):
    try:
    
        response = es.search(index=INDEX_NAME,
                             query={
                            "match": {
                                "content": str(query)
                            }
                                 },)
        return response["hits"]["hits"]
    except Exception as e:
        print(f"Error searching documents: {e}")
        raise