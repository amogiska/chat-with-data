import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
    
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "")
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DATABASE: str = os.getenv("CLICKHOUSE_DATABASE", "default")
    CLICKHOUSE_SECURE: bool = os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
    
    MIN_RECORDS_PER_GROUP: int = int(os.getenv("MIN_RECORDS_PER_GROUP", "10"))
    MAX_DIMENSION_PAIRS: int = int(os.getenv("MAX_DIMENSION_PAIRS", "10"))
    EMBEDDINGS_TABLE: str = os.getenv("EMBEDDINGS_TABLE", "aggregate_embeddings")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required")
        if not cls.CLICKHOUSE_HOST:
            raise ValueError("CLICKHOUSE_HOST required")
        if not cls.CLICKHOUSE_PASSWORD:
            raise ValueError("CLICKHOUSE_PASSWORD required")
        return True
    
    @classmethod
    def get_embedding_cost_per_1k(cls) -> float:
        costs = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.00010,
        }
        return costs.get(cls.EMBEDDING_MODEL, 0.00002)


class StrategyConfig:
    ENABLE_SINGLE_DIMENSION: bool = True
    ENABLE_DIMENSION_PAIRS: bool = True
    ENABLE_TEMPORAL_PATTERNS: bool = True
    
    TEMPORAL_GRANULARITIES = ['hour', 'day_of_week', 'day_of_month', 'month']


