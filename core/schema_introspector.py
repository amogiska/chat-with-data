"""Schema introspection for ClickHouse tables."""
from typing import List, Dict, Any
from dataclasses import dataclass
import clickhouse_connect


@dataclass
class ColumnInfo:
    """Information about a table column."""
    name: str
    type: str
    base_type: str  # Type without Nullable() wrapper
    is_nullable: bool
    default_kind: str
    comment: str
    
    def __repr__(self):
        nullable = "Nullable" if self.is_nullable else ""
        return f"Column({self.name}: {nullable}{self.base_type})"


class SchemaIntrospector:
    """Introspects ClickHouse table schemas."""
    
    def __init__(self, client: clickhouse_connect.driver.Client):
        self.client = client
    
    def get_table_schema(self, table_name: str, database: str = None) -> List[ColumnInfo]:
        """
        Retrieve schema information for a table.
        
        Args:
            table_name: Name of the table to introspect
            database: Database name (uses current database if None)
            
        Returns:
            List of ColumnInfo objects describing each column
        """
        database_clause = f"AND database = '{database}'" if database else "AND database = currentDatabase()"
        
        query = f"""
        SELECT 
            name,
            type,
            default_kind,
            comment
        FROM system.columns
        WHERE table = '{table_name}'
        {database_clause}
        ORDER BY position
        """
        
        result = self.client.query(query)
        columns = []
        
        for row in result.result_rows:
            name, type_str, default_kind, comment = row
            
            # Parse type to extract base type and nullable info
            is_nullable = type_str.startswith('Nullable(')
            base_type = self._extract_base_type(type_str)
            
            columns.append(ColumnInfo(
                name=name,
                type=type_str,
                base_type=base_type,
                is_nullable=is_nullable,
                default_kind=default_kind or '',
                comment=comment or ''
            ))
        
        if not columns:
            raise ValueError(f"Table '{table_name}' not found or has no columns")
        
        return columns
    
    def _extract_base_type(self, type_str: str) -> str:
        """
        Extract base type from ClickHouse type string.
        
        Examples:
            'Nullable(Float64)' -> 'Float64'
            'LowCardinality(String)' -> 'String'
            'Enum8('CSH' = 1, 'CRE' = 2)' -> 'Enum8'
            'Array(Float32)' -> 'Array(Float32)'
        """
        # Handle Nullable
        if type_str.startswith('Nullable('):
            type_str = type_str[9:-1]  # Remove 'Nullable(' and ')'
        
        # Handle LowCardinality
        if type_str.startswith('LowCardinality('):
            type_str = type_str[15:-1]  # Remove 'LowCardinality(' and ')'
        
        # Handle Enum - extract just 'Enum8' or 'Enum16'
        if type_str.startswith('Enum'):
            if '(' in type_str:
                type_str = type_str[:type_str.index('(')]
        
        return type_str
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get approximate row count for a table."""
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.client.query(query)
        return result.result_rows[0][0]
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample rows from the table.
        
        Args:
            table_name: Table to sample from
            limit: Number of rows to retrieve
            
        Returns:
            List of dictionaries, one per row
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        result = self.client.query(query)
        
        samples = []
        for row in result.result_rows:
            row_dict = dict(zip(result.column_names, row))
            samples.append(row_dict)
        
        return samples


