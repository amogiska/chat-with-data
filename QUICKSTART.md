# Quick Start Guide

## Setup (5 minutes)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create `.env` file
```bash
cat > .env << EOF
OPENAI_API_KEY=your_actual_api_key_here
CLICKHOUSE_HOST=xrotjcr0k2.us-west-2.aws.clickhouse.cloud
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=..sWZzia6GGts
EOF
```

### 3. Test connection
```bash
python main.py --test-connection
```

## Run the Pipeline

### Option 1: Dry Run (Recommended First)
See what will happen without spending money:
```bash
python main.py trips --dry-run
```

### Option 2: List Strategies
See all available aggregation strategies:
```bash
python main.py trips --list-strategies
```

### Option 3: Full Run
Generate all embeddings:
```bash
python main.py trips
```

### Option 4: Run Specific Strategies
Only generate embeddings for specific aggregations:
```bash
python main.py trips --strategies by_pickup_ntaname,by_dropoff_ntaname
```

## Query the Embeddings

After generating embeddings, search them:

```bash
# Find routes with high tips
python query_embeddings.py "routes with high tips"

# Find weekend patterns
python query_embeddings.py "weekend trip patterns" --top-k 10

# Find expensive trips
python query_embeddings.py "expensive long distance trips"
```

## Expected Output

### Dry Run
```
============================================================
Embedding Pipeline for table: trips
============================================================

Step 1: Initializing components...
Step 2: Introspecting table schema...
✓ Found 16 columns

Step 3: Detecting dimensions...
Dimensions(
  categorical=2: ['pickup_ntaname', 'dropoff_ntaname']
  temporal=2: ['pickup_datetime', 'dropoff_datetime']
  numeric=8: ['trip_distance', 'fare_amount', ...]
)

Step 4: Generating aggregation strategies...
✓ Generated 12 strategies

Step 5: Estimating work...
  Total aggregations: ~2,450
  Estimated cost: $0.0049
  Estimated tokens: ~245,000

[DRY RUN] Stopping here.
```

### Full Run
Same as above, plus:
```
Step 6: Executing pipeline...
Processing strategies: 100%|████████████| 12/12 [00:45<00:00]

Pipeline Complete!
Total embeddings generated: 2,450
Total cost: $0.0049
```

### Query Results
```
Searching embeddings for: 'routes with high tips'
============================================================

Found 5 results:

1. Similarity: 0.892 | Distance: 0.108
   Strategy: by_pickup_ntaname_and_dropoff_ntaname
   Source: trips

   Summary:
   Group: Pickup Ntaname: Upper East Side, Dropoff Ntaname: JFK Airport
   Total records: 1,234
   Trip Distance: avg 16.8 miles
   Fare Amount: avg $52.30, median $51.20
   Tip Amount: avg $12.45, median $11.80 (high tipping!)

   Metadata:
    Records: 1,234
    avg_tip_amount: 12.45
    avg_fare_amount: 52.30
```

## What Table Name to Use?

The table name depends on your ClickHouse setup. Common possibilities:
- `trips`
- `trips_table`
- `nyc_taxi_trips`
- `default.trips`

To find your table:
```sql
-- Run this in ClickHouse
SHOW TABLES;
```

Or if you know your table has the taxi trip data, just use that name!

## Troubleshooting

### "Table not found"
- Check your table name: `SHOW TABLES` in ClickHouse
- Specify database: `python main.py database.table_name`

### "OPENAI_API_KEY is required"
- Create `.env` file with your API key
- Or: `export OPENAI_API_KEY=your_key`

### "Connection failed"
- Verify ClickHouse credentials in `.env`
- Test: `python main.py --test-connection`

### "Rate limit exceeded"
- The pipeline includes retry logic with exponential backoff
- If persistent, reduce `EMBEDDING_BATCH_SIZE` in config.py

## Cost Considerations

Typical costs for different table sizes:

| Aggregations | Tokens | Cost (3-small) | Cost (3-large) |
|-------------|--------|----------------|----------------|
| 100 | ~10K | $0.0002 | $0.0013 |
| 1,000 | ~100K | $0.002 | $0.013 |
| 10,000 | ~1M | $0.020 | $0.130 |

Always run `--dry-run` first to see estimated costs!

## Next Steps

1. ✅ Run dry run on your table
2. ✅ Review the strategies that will be generated
3. ✅ Run the full pipeline
4. ✅ Try querying the embeddings
5. 🚀 Build a chat interface using the embeddings!

## Need Help?

Check the main README.md for:
- Detailed architecture
- Configuration options
- API reference
- Advanced usage


