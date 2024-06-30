from elasticsearch import Elasticsearch, exceptions

class ElasticsearchHandler:
    """ handles elasticsearch logic"""

    dynamic_templates =    [
            {
                "float_values": {
                    "match_mapping_type": "long",
                    "path_match": "*.global.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            },
            {
                "float_values": {
                    "match_mapping_type": "double",
                    "path_match": "*.global.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            },
            {
                "float_values": {
                    "match_mapping_type": "long",
                    "path_match": "*.by_instrument.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            },
            {
                "float_values": {
                    "match_mapping_type": "double",
                    "path_match": "*.by_instrument.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            },
            {
                "float_values": {
                    "match_mapping_type": "long",
                    "path_match": "*.maps.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            },
            {
                "float_values": {
                    "match_mapping_type": "double",
                    "path_match": "*.maps.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            },
            {
                "float_values": {
                    "match_mapping_type": "long",
                    "path_match": "*.ticks.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            },
            {
                "float_values": {
                    "match_mapping_type": "double",
                    "path_match": "*.ticks.*",
                    "mapping": {
                        "type": "float"
                    }
                }
            }
        ]

    def __init__(self, es_host="http://localhost:9200", username="elastic", password="None"):
        self.es = Elasticsearch(
            es_host,
            http_auth=(username, password),
        )
        self.check_connection()

    def check_connection(self):
        """ checks if elasticsearch database is connected"""
        try:
            if self.es.ping():
                print("Connected to Elasticsearch")
            else:
                print("Could not connect to Elasticsearch")
        except exceptions.AuthenticationException as e:
            print(f"Authentication failed: {e}")
        except exceptions.ConnectionError as e:
            print(f"Connection failed: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def create_schema(self, properties, number_of_shards=5, number_of_replicas=0):
        """ creates schema"""
        es_schema  = {
            "settings": {
                "number_of_shards": number_of_shards,
                "number_of_replicas": number_of_replicas,
                },
        }
        return es_schema 

    def create_index(self, index_name, schema=None):
        """ creates'database'"""
        try:
            if not self.es.indices.exists(index=index_name):
                if schema:
                    self.es.indices.create(index=index_name, body=schema)
                else:
                    self.es.indices.create(index=index_name)
                print(f"Index '{index_name}' created.")
            else:
                print(f"Index '{index_name}' already exists.")
        except Exception as e:
            print(f"An error occurred while creating the index: {e}")

    def delete_index(self, index_name):
        """ deletes index"""
        try:
            if self.es.indices.exists(index=index_name):
                self.es.indices.delete(index=index_name)
                print(f"Index '{index_name}' deleted.")
            else:
                print(f"Index '{index_name}' does not exist.")
        except Exception as e:
            print(f"An error occurred while deleting the index: {e}")

    def add_document(self, index_name, doc_id, document):
        """ adds document to index"""
        try:
            res = self.es.index(index=index_name, id=doc_id, document=document)
            print(f"Document {doc_id} added: {res['result']}")
        except Exception as e:
            print(f"An error occurred while adding document {doc_id}: {e}")

    def delete_document(self, index_name, doc_id):
        """ deletes document from index"""
        try:
            res = self.es.delete(index=index_name, id=doc_id)
            print(f"Document {doc_id} deleted: {res['result']}")
        except Exception as e:
            print(f"An error occurred while deleting document {doc_id}: {e}")

    def search_documents(self, index_name, query):
        """ searches for documents"""
        try:
            res = self.es.search(index=index_name, query=query)
            print("Search results:", res["hits"]["hits"])
        except Exception as e:
            print(f"An error occurred while searching for documents: {e}")