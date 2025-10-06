"""Manage storage of embeddings in ClickHouse."""
from typing import List, Dict, Any, Optional
import json
import clickhouse_connect
from config import Config


class StorageManager:
    """Handles storage of embeddings in ClickHouse."""
    
    def __init__(self, client: clickhouse_connect.driver.Client, table_name: str = None):
        self.client = client
        self.table_name = table_name or Config.EMBEDDINGS_TABLE
    
    def create_embeddings_table(self, embedding_dimension: int = 1536):
        """
        Create the table for storing embeddings if it doesn't exist.
        
        Args:
            embedding_dimension: Dimension of the embedding vectors
        """
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
        """
        Insert embeddings into ClickHouse.
        
        Args:
            embeddings: List of embedding dictionaries with required fields
            source_table: Name of the source table these embeddings came from
        """
        if not embeddings:
            return
        
        # Prepare data for insertion
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
        
        # Insert in batches
        column_names = ['id', 'strategy_name', 'summary_text', 'embedding', 
                       'metadata', 'source_table', 'record_count']
        
        self.client.insert(
            self.table_name,
            insert_data,
            column_names=column_names
        )
        
        print(f"✓ Inserted {len(embeddings)} embeddings")
    
    def check_existing_embeddings(self, strategy_name: str, source_table: str) -> int:
        """
        Check how many embeddings already exist for a strategy.
        
        Args:
            strategy_name: Name of the aggregation strategy
            source_table: Source table name
            
        Returns:
            Count of existing embeddings
        """
        query = f"""
        SELECT COUNT(*) 
        FROM {self.table_name}
        WHERE strategy_name = '{strategy_name}' 
        AND source_table = '{source_table}'
        """
        
        result = self.client.query(query)
        return result.result_rows[0][0]
    
    def delete_embeddings(self, strategy_name: str = None, source_table: str = None):
        """
        Delete embeddings, optionally filtered by strategy or source table.
        
        Args:
            strategy_name: Optional strategy name filter
            source_table: Optional source table filter
        """
        conditions = []
        if strategy_name:
            conditions.append(f"strategy_name = '{strategy_name}'")
        if source_table:
            conditions.append(f"source_table = '{source_table}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        delete_query = f"""
        ALTER TABLE {self.table_name} 
        DELETE WHERE {where_clause}
        """
        
        self.client.command(delete_query)
        print(f"✓ Deleted embeddings matching: {where_clause}")
    
    def get_embeddings_summary(self, source_table: str = None) -> List[Dict[str, Any]]:
        """
        Get summary statistics about stored embeddings.
        
        Args:
            source_table: Optional filter by source table
            
        Returns:
            List of summary dictionaries
        """
        where_clause = f"WHERE source_table = '{source_table}'" if source_table else ""
        
        query = f"""
        SELECT 
            source_table,
            strategy_name,
            COUNT(*) as embedding_count,
            SUM(record_count) as total_records_represented,
            MIN(created_at) as first_created,
            MAX(created_at) as last_created
        FROM {self.table_name}
        {where_clause}
        GROUP BY source_table, strategy_name
        ORDER BY source_table, strategy_name
        """
        
        result = self.client.query(query)
        
        summaries = []
        for row in result.result_rows:
            summaries.append({
                'source_table': row[0],
                'strategy_name': row[1],
                'embedding_count': row[2],
                'total_records_represented': row[3],
                'first_created': row[4],
                'last_created': row[5]
            })
        
        return summaries
    
    def search_similar(self, 
                      query_embedding: List[float], 
                      top_k: int = 10,
                      source_table: str = None) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            source_table: Optional filter by source table
            
        Returns:
            List of similar embedding results with scores
        """
        where_clause = f"WHERE source_table = '{source_table}'" if source_table else ""
        
        # Convert embedding to array format for ClickHouse
        embedding_str = str(query_embedding)
        
        query = f"""
        SELECT 
            id,
            strategy_name,
            summary_text,
            metadata,
            source_table,
            record_count,
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


