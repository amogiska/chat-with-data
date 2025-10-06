from typing import List
from dataclasses import dataclass
import clickhouse_connect


@dataclass
class ColumnInfo:
    name: str
    type: str
    base_type: str
    is_nullable: bool
    default_kind: str
    comment: str
    
    def __repr__(self):
        nullable = "Nullable" if self.is_nullable else ""
        return f"Column({self.name}: {nullable}{self.base_type})"


class SchemaIntrospector:
    def __init__(self, client: clickhouse_connect.driver.Client):
        self.client = client
    
    def get_table_schema(self, table_name: str, database: str = None) -> List[ColumnInfo]:
        database_clause = f"AND database = '{database}'" if database else "AND database = currentDatabase()"
        
        query = f"""
        SELECT name, type, default_kind, comment
        FROM system.columns
        WHERE table = '{table_name}'
        {database_clause}
        ORDER BY position
        """
        
        result = self.client.query(query)
        columns = []
        
        for row in result.result_rows:
            name, type_str, default_kind, comment = row
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
        if type_str.startswith('Nullable('):
            type_str = type_str[9:-1]
        
        if type_str.startswith('LowCardinality('):
            type_str = type_str[15:-1]
        
        if type_str.startswith('Enum'):
            if '(' in type_str:
                type_str = type_str[:type_str.index('(')]
        
        return type_str
    
    def get_table_row_count(self, table_name: str) -> int:
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.client.query(query)
        return result.result_rows[0][0]
