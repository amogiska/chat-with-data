"""Configuration management for the embedding pipeline."""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Global configuration for the embedding pipeline."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
    
    # ClickHouse Configuration
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "")
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DATABASE: str = os.getenv("CLICKHOUSE_DATABASE", "default")
    CLICKHOUSE_SECURE: bool = os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
    
    # Pipeline Configuration
    MIN_RECORDS_PER_GROUP: int = int(os.getenv("MIN_RECORDS_PER_GROUP", "10"))
    MAX_DIMENSION_PAIRS: int = int(os.getenv("MAX_DIMENSION_PAIRS", "10"))
    
    # Storage Configuration
    EMBEDDINGS_TABLE: str = os.getenv("EMBEDDINGS_TABLE", "aggregate_embeddings")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Set it in .env file or ~/.zshrc")
        if not cls.CLICKHOUSE_HOST:
            raise ValueError("CLICKHOUSE_HOST is required. Set it in .env file or ~/.zshrc")
        if not cls.CLICKHOUSE_PASSWORD:
            raise ValueError("CLICKHOUSE_PASSWORD is required. Set it in .env file or ~/.zshrc")
        return True
    
    @classmethod
    def get_embedding_cost_per_1k(cls) -> float:
        """Get cost per 1000 tokens for the selected embedding model."""
        costs = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.00010,
        }
        return costs.get(cls.EMBEDDING_MODEL, 0.00002)


# Aggregation Strategy Configuration
class StrategyConfig:
    """Configuration for aggregation strategies."""
    
    ENABLE_SINGLE_DIMENSION: bool = True
    ENABLE_DIMENSION_PAIRS: bool = True
    ENABLE_TEMPORAL_PATTERNS: bool = True
    
    # Temporal granularities to generate
    TEMPORAL_GRANULARITIES = [
        'hour',           # Hour of day (0-23)
        'day_of_week',    # Day of week (1-7)
        'day_of_month',   # Day of month (1-31)
        'month',          # Month (1-12)
    ]


