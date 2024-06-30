from config import elastic_password
from dbhandler.db_elastic import ElasticsearchHandler
import time
if __name__ == "__main__":
    es_handler = ElasticsearchHandler(password=elastic_password)

    # Create an index with a specific schema
    schema = {
        "settings": {
            "number_of_shards": 5,
            "number_of_replicas": 1
        },
        "mappings": {
            "properties": {
                "value": {
                    "type": "float"
                },
                "books": {"type": "object", "dynamic": True, "properties":{}},
            }
        }
    }
    es_handler.create_index("test-index", schema)

    # Add documents
    documents = [
        {"id": 1, "name": "John Doe", "age": 30, "email": "johndoe@example.com"},
        {"id": 2, "name": "Jane Smith", "age": 25, "email": "janesmith@example.com"}
    ]

    for doc in documents:
        es_handler.add_document("test-index", doc["id"], doc)

    # Search for documents
    query = {"match_all": {}}
    time.sleep(1)
    es_handler.search_documents("test-index", query)

    # Delete a document
    es_handler.delete_document("test-index", 1)

    # Delete the index
    es_handler.delete_index("test-index")