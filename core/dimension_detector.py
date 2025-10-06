from typing import List, Dict, Set
from dataclasses import dataclass, field
from .schema_introspector import ColumnInfo


@dataclass
class Dimensions:
    categorical: List[str] = field(default_factory=list)
    temporal: List[str] = field(default_factory=list)
    numeric: List[str] = field(default_factory=list)
    geospatial: Dict[str, List[str]] = field(default_factory=dict)
    
    def __repr__(self):
        return (f"Dimensions(\n"
                f"  categorical={len(self.categorical)}: {self.categorical[:3]}\n"
                f"  temporal={len(self.temporal)}: {self.temporal}\n"
                f"  numeric={len(self.numeric)}: {self.numeric[:5]}\n"
                f"  geospatial={len(self.geospatial)}: {list(self.geospatial.keys())}\n"
                f")")


class DimensionDetector:
    CATEGORICAL_TYPES = {
        'String', 'FixedString', 'Enum8', 'Enum16', 
        'UUID', 'IPv4', 'IPv6'
    }
    
    TEMPORAL_TYPES = {
        'Date', 'Date32', 'DateTime', 'DateTime64'
    }
    
    NUMERIC_TYPES = {
        'UInt8', 'UInt16', 'UInt32', 'UInt64', 'UInt128', 'UInt256',
        'Int8', 'Int16', 'Int32', 'Int64', 'Int128', 'Int256',
        'Float32', 'Float64',
        'Decimal', 'Decimal32', 'Decimal64', 'Decimal128', 'Decimal256'
    }
    
    EXCLUDE_PATTERNS = {
        'id', 'uuid', 'hash', 'token', 'key', 
        'created_at', 'updated_at', 'deleted_at',
        'timestamp', 'version'
    }
    
    def detect(self, columns: List[ColumnInfo]) -> Dimensions:
        dimensions = Dimensions()
        
        for col in columns:
            col_lower = col.name.lower()
            
            if any(pattern in col_lower for pattern in self.EXCLUDE_PATTERNS):
                continue
            
            if self._is_categorical(col):
                dimensions.categorical.append(col.name)
            elif self._is_temporal(col):
                dimensions.temporal.append(col.name)
            elif self._is_numeric(col):
                dimensions.numeric.append(col.name)
        
        dimensions.geospatial = self._detect_geospatial_pairs(columns)
        
        return dimensions
    
    def _is_categorical(self, col: ColumnInfo) -> bool:
        if col.base_type in self.CATEGORICAL_TYPES:
            return True
        if 'String' in col.base_type:
            return True
        if col.base_type.startswith('Enum'):
            return True
        return False
    
    def _is_temporal(self, col: ColumnInfo) -> bool:
        if col.base_type in self.TEMPORAL_TYPES:
            return True
        if any(dt in col.base_type for dt in ['Date', 'Time']):
            return True
        return False
    
    def _is_numeric(self, col: ColumnInfo) -> bool:
        base = col.base_type
        if any(base.startswith(nt) for nt in ['UInt', 'Int', 'Float', 'Decimal']):
            return True
        if base in self.NUMERIC_TYPES:
            return True
        return False
    
    def _detect_geospatial_pairs(self, columns: List[ColumnInfo]) -> Dict[str, List[str]]:
        pairs = {}
        col_names = {col.name.lower(): col.name for col in columns}
        prefixes = self._extract_geospatial_prefixes(col_names)
        
        for prefix in prefixes:
            lon_key = f'{prefix}longitude' if prefix else 'longitude'
            lat_key = f'{prefix}latitude' if prefix else 'latitude'
            
            if lon_key in col_names and lat_key in col_names:
                pair_name = prefix.rstrip('_') if prefix else 'location'
                pairs[pair_name] = [col_names[lon_key], col_names[lat_key]]
        
        return pairs
    
    def _extract_geospatial_prefixes(self, col_names_lower: Dict[str, str]) -> Set[str]:
        prefixes = set([''])
        
        for col_lower in col_names_lower.keys():
            if 'longitude' in col_lower:
                prefix = col_lower.replace('longitude', '')
                prefixes.add(prefix)
            elif 'latitude' in col_lower:
                prefix = col_lower.replace('latitude', '')
                prefixes.add(prefix)
        
        return prefixes
