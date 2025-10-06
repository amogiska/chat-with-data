# Chat with Data

A generalized pipeline for generating aggregate embeddings from ClickHouse tables using OpenAI's embedding API.

## Overview

This tool automatically:
1. **Introspects** your ClickHouse table schema
2. **Detects** useful dimensions (categorical, temporal, numeric, geospatial)
3. **Generates** meaningful aggregation strategies
4. **Executes** SQL aggregations on your data
5. **Converts** aggregations to natural language descriptions
6. **Creates** embeddings using OpenAI's API
7. **Stores** embeddings in ClickHouse for semantic search

Instead of creating embeddings for millions of individual rows, this approach creates embeddings of **aggregated insights**, making it perfect for analytical queries like:
- "Which routes have the highest tips?"
- "What are the patterns in weekend trips?"
- "Show me neighborhoods with long-distance trips"

## Features

✅ **Fully Generalized** - Works with any ClickHouse table  
✅ **Automatic Discovery** - No manual configuration needed  
✅ **Multiple Strategies** - Single dimensions, pairs, temporal patterns  
✅ **Cost Efficient** - Aggregates first, then embeds (much cheaper)  
✅ **Semantic Search** - Query using natural language  
✅ **Resumable** - Can stop and restart without duplicates  
✅ **Observable** - Progress bars and detailed statistics  

## Installation

### 1. Clone or download this repository

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ClickHouse Configuration
CLICKHOUSE_HOST=your_host.clickhouse.cloud
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_password_here
CLICKHOUSE_DATABASE=default
```

## Usage

### Basic Usage

```bash
# Run full pipeline on a table
python main.py trips

# Dry run to see what would happen (no cost)
python main.py trips --dry-run

# List available strategies for a table
python main.py trips --list-strategies

# Run specific strategies only
python main.py trips --strategies by_pickup_ntaname,by_route

# Test ClickHouse connection
python main.py --test-connection
```

### Example Output

```
============================================================
Embedding Pipeline for table: trips
============================================================

Step 1: Initializing components...
✓ Created/verified embeddings table: aggregate_embeddings

Step 2: Introspecting table schema...
✓ Found 16 columns

Step 3: Detecting dimensions...
Dimensions(
  categorical=2: ['pickup_ntaname', 'dropoff_ntaname']
  temporal=2: ['pickup_datetime', 'dropoff_datetime']
  numeric=8: ['trip_distance', 'fare_amount', 'tip_amount', ...]
  geospatial=2: ['pickup', 'dropoff']
)

Step 4: Generating aggregation strategies...
✓ Generated 12 strategies

Step 5: Estimating work...
  Total aggregations: ~2,450
  Estimated cost: $0.0049
  Estimated tokens: ~245,000

Step 6: Executing pipeline...
Processing strategies: 100%|████████████| 12/12 [00:45<00:00]

✓ Inserted 2,450 embeddings

Step 7: Summary
============================================================
Pipeline Complete!
============================================================
Table: trips
Total embeddings generated: 2,450
Strategies executed: 12
Strategies failed: 0

Embedding API Stats:
  Total requests: 25
  Total tokens: 243,120
  Total cost: $0.0049
  Model: text-embedding-3-small
  Dimension: 1536
```

## Project Structure

```
chat-with-data/
├── .env                          # Environment variables (gitignored)
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── config.py                     # Configuration management
├── clickhouse_client.py          # ClickHouse utilities
├── main.py                       # CLI entry point
├── pipeline.py                   # Main orchestrator
│
└── core/                         # Core components
    ├── __init__.py
    ├── schema_introspector.py    # Table schema discovery
    ├── dimension_detector.py     # Column classification
    ├── aggregation_generator.py  # SQL generation
    ├── text_generator.py         # Natural language conversion
    ├── embedding_generator.py    # OpenAI API integration
    └── storage_manager.py        # ClickHouse storage
```

## How It Works

### 1. Schema Introspection
Queries `system.columns` to understand your table structure, including column types, nullable fields, and more.

### 2. Dimension Detection
Automatically classifies columns:
- **Categorical**: Strings, Enums, LowCardinality - good for GROUP BY
- **Temporal**: Date/DateTime fields - for time-based patterns
- **Numeric**: Numbers - for aggregations (AVG, MIN, MAX, etc.)
- **Geospatial**: Longitude/latitude pairs - for location analysis

### 3. Aggregation Strategies
Generates multiple strategies:
- **Single dimension**: Group by each categorical column
- **Dimension pairs**: Combinations like route (pickup → dropoff)
- **Temporal patterns**: Hour of day, day of week, month

### 4. Natural Language Generation
Converts aggregated data into readable text:

```
Group: Pickup Ntaname: East Harlem, Dropoff Ntaname: Midtown
Total records: 1,234
Trip Distance: avg 3.2 miles, median 2.8 miles, range [0.5 - 12.3]
Fare Amount: avg $12.45, median $11.20, range [$5.00 - $45.00]
Tip Amount: avg $2.10, median $1.80, range [$0.00 - $15.00]
```

### 5. Embedding Generation
Uses OpenAI's API (default: `text-embedding-3-small`) to convert text to vectors.

### 6. Storage
Stores in ClickHouse with this schema:

```sql
CREATE TABLE aggregate_embeddings (
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
```

## Configuration Options

Edit `config.py` or use environment variables:

```python
# Embedding model (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
EMBEDDING_MODEL = "text-embedding-3-small"

# Batch size for OpenAI API calls
EMBEDDING_BATCH_SIZE = 100

# Minimum records per aggregation group
MIN_RECORDS_PER_GROUP = 10

# Maximum dimension pairs to generate
MAX_DIMENSION_PAIRS = 10

# Table name for storing embeddings
EMBEDDINGS_TABLE = "aggregate_embeddings"
```

## Querying Embeddings

After generating embeddings, you can search them using the `StorageManager`:

```python
from clickhouse_client import get_client
from core import StorageManager, EmbeddingGenerator

# Get clients
client = get_client()
storage = StorageManager(client)
embedding_gen = EmbeddingGenerator()

# Create query embedding
query_text = "routes with high tips"
query_embedding = embedding_gen.generate_embeddings([query_text])[0]

# Search for similar aggregations
results = storage.search_similar(
    query_embedding=query_embedding,
    top_k=10,
    source_table='trips'
)

# Display results
for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Strategy: {result['strategy_name']}")
    print(f"Summary: {result['summary_text']}")
    print()
```

## Cost Estimation

Costs depend on the embedding model and number of aggregations:

| Model | Cost per 1M tokens | Typical cost for 2,500 aggregations |
|-------|-------------------|-------------------------------------|
| text-embedding-3-small | $0.02 | ~$0.005 |
| text-embedding-3-large | $0.13 | ~$0.032 |
| text-embedding-ada-002 | $0.10 | ~$0.025 |

The pipeline shows estimated costs before running.

## Limitations

- Requires ClickHouse with system table access
- OpenAI API key required
- Best for analytical queries, not individual record search
- Cost scales with number of unique aggregation groups

## Future Enhancements

- [ ] Support for other embedding providers (Cohere, HuggingFace)
- [ ] Built-in query interface for semantic search
- [ ] Web UI for exploring embeddings
- [ ] Export embeddings to vector databases (Pinecone, Weaviate)
- [ ] Incremental updates (only process new data)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
