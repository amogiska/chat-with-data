# Chat with Data

Generate embeddings from ClickHouse table aggregations for semantic search over analytical insights.

## Overview

Instead of embedding individual rows (expensive, not useful for analytics), this tool:
1. Aggregates your data (by neighborhoods, routes, time patterns, etc.)
2. Converts aggregations to natural language
3. Generates embeddings of these summaries
4. Stores them in ClickHouse for semantic search

**Example**: Query "routes with high tips" → finds "Upper East Side → JFK Airport: 1,234 trips, avg tip $12.45"

## Setup

### Install dependencies
```bash
pip install -r requirements.txt
```

### Configure credentials

Add to `~/.zshrc`:
```bash
export CLICKHOUSE_HOST="your_host.clickhouse.cloud"
export CLICKHOUSE_PASSWORD="your_password"
export OPENAI_API_KEY="your_openai_key"
```

Or create `.env`:
```
CLICKHOUSE_HOST=your_host.clickhouse.cloud
CLICKHOUSE_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
```

### Test connection
```bash
python main.py --test-connection
```

## Usage

### Generate embeddings

```bash
# Preview (free, no API calls)
python main.py your_table --dry-run

# See available strategies
python main.py your_table --list-strategies

# Generate all embeddings
python main.py your_table

# Generate specific strategies only
python main.py your_table --strategies by_route,by_hour
```

### Query embeddings

```bash
python query_embeddings.py "routes with high tips"
python query_embeddings.py "weekend patterns" --top-k 10
python query_embeddings.py "expensive trips"
```

## How it works

```
ClickHouse Table
    ↓
Schema introspection (detect columns/types)
    ↓
Dimension detection (categorical, temporal, numeric)
    ↓
Strategy generation (routes, hourly, neighborhoods)
    ↓
SQL aggregation (GROUP BY queries)
    ↓
Text generation (natural language summaries)
    ↓
OpenAI embeddings (vectors)
    ↓
ClickHouse storage (searchable)
```

## Example

For a taxi trips table:

**Input**: 2M trip records

**Generates**:
- 7,272 route embeddings (pickup → dropoff)
- 24 hourly pattern embeddings
- 7 day-of-week embeddings
- 186 neighborhood embeddings

**Query**: "routes with high tips"

**Result**:
```
Route: Upper East Side → JFK Airport
Total trips: 1,234
Avg fare: $52.30
Avg tip: $12.45 (24% tip rate)
Distance: 16.8 miles
```

## Configuration

Environment variables or `.env`:

```bash
# OpenAI
OPENAI_API_KEY=required
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=100

# ClickHouse
CLICKHOUSE_HOST=required
CLICKHOUSE_PASSWORD=required
CLICKHOUSE_USER=default
CLICKHOUSE_DATABASE=default

# Pipeline
MIN_RECORDS_PER_GROUP=10
MAX_DIMENSION_PAIRS=10
EMBEDDINGS_TABLE=aggregate_embeddings
```

## Requirements

- Python 3.9+
- ClickHouse with system tables access
- OpenAI API key

