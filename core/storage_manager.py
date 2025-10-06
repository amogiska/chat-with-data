from typing import List, Dict, Any
import json
import clickhouse_connect
from config import Config


class StorageManager:
    def __init__(self, client: clickhouse_connect.driver.Client, table_name: str = None):
        self.client = client
        self.table_name = table_name or Config.EMBEDDINGS_TABLE
    
    def create_embeddings_table(self, embedding_dimension: int = 1536):
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id String,
            strategy_name String,
            summary_text String,
            embedding Array(Float32),
            metadata String,
            source_table String,
            record_count UInt64,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (strategy_name, id)
        """
        
        self.client.command(create_query)
        print(f"✓ Created/verified embeddings table: {self.table_name}")
    
    def insert_embeddings(self, embeddings: List[Dict[str, Any]], source_table: str):
        if not embeddings:
            return
        
        insert_data = []
        for emb in embeddings:
            row = (
                emb['id'],
                emb['strategy_name'],
                emb['text'],
                emb['embedding'],
                json.dumps(emb.get('metadata', {})),
                source_table,
                emb.get('metadata', {}).get('record_count', 0)
            )
            insert_data.append(row)
        
        column_names = ['id', 'strategy_name', 'summary_text', 'embedding', 
                       'metadata', 'source_table', 'record_count']
        
        self.client.insert(self.table_name, insert_data, column_names=column_names)
        print(f"✓ Inserted {len(embeddings)} embeddings")
    
    def search_similar(self, query_embedding: List[float], top_k: int = 10,
                      source_table: str = None) -> List[Dict[str, Any]]:
        where_clause = f"WHERE source_table = '{source_table}'" if source_table else ""
        embedding_str = str(query_embedding)
        
        query = f"""
        SELECT 
            id, strategy_name, summary_text, metadata, source_table, record_count,
            cosineDistance(embedding, {embedding_str}) as distance,
            1 - cosineDistance(embedding, {embedding_str}) as similarity
        FROM {self.table_name}
        {where_clause}
        ORDER BY distance ASC
        LIMIT {top_k}
        """
        
        result = self.client.query(query)
        
        results = []
        for row in result.result_rows:
            results.append({
                'id': row[0],
                'strategy_name': row[1],
                'summary_text': row[2],
                'metadata': json.loads(row[3]),
                'source_table': row[4],
                'record_count': row[5],
                'distance': row[6],
                'similarity': row[7]
            })
        
        return results
