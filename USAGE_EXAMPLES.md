# Usage Examples

## Real-World Examples for Your Taxi Data

### 1. Generate All Embeddings

```bash
python main.py trips
```

**What happens:**
- Discovers 16 columns in your trips table
- Detects 2 categorical (pickup_ntaname, dropoff_ntaname)
- Detects 2 temporal (pickup_datetime, dropoff_datetime)  
- Detects 8 numeric columns (fare, distance, tips, etc.)
- Generates 12+ aggregation strategies
- Creates ~2,500 embeddings
- Cost: ~$0.005

### 2. Preview What Will Happen (FREE)

```bash
python main.py trips --dry-run
```

**Output:**
```
Detected Dimensions:
  categorical=2: ['pickup_ntaname', 'dropoff_ntaname']
  temporal=2: ['pickup_datetime', 'dropoff_datetime']
  numeric=8: ['trip_distance', 'fare_amount', 'tip_amount', ...]

Generated 12 strategies:
  • by_pickup_ntaname
  • by_dropoff_ntaname
  • by_pickup_ntaname_and_dropoff_ntaname (routes!)
  • by_pickup_datetime_hour
  • by_pickup_datetime_day_of_week
  • by_pickup_datetime_month
  • ... and more

Estimated:
  Total aggregations: ~2,450
  Estimated cost: $0.0049
  Estimated tokens: ~245,000
```

### 3. See Available Strategies

```bash
python main.py trips --list-strategies
```

**Shows all strategies that will be generated:**
```
Available Strategies (12 total):

  • by_pickup_ntaname
    Description: Aggregated by pickup_ntaname
    Groups by: pickup_ntaname

  • by_dropoff_ntaname
    Description: Aggregated by dropoff_ntaname
    Groups by: dropoff_ntaname

  • by_pickup_ntaname_and_dropoff_ntaname
    Description: Aggregated by pickup_ntaname and dropoff_ntaname
    Groups by: pickup_ntaname, dropoff_ntaname

  • by_pickup_datetime_hour
    Description: Aggregated by hour from pickup_datetime
    Groups by: hour_of_day
  
  ... etc
```

### 4. Generate Specific Strategies Only

```bash
# Only generate route embeddings (pickup → dropoff)
python main.py trips --strategies by_pickup_ntaname_and_dropoff_ntaname

# Multiple strategies
python main.py trips --strategies by_pickup_ntaname,by_dropoff_ntaname,by_pickup_datetime_hour
```

## Querying Examples

### Find Routes with High Tips

```bash
python query_embeddings.py "routes with high tips"
```

**Example Result:**
```
1. Similarity: 0.892
   Strategy: by_pickup_ntaname_and_dropoff_ntaname
   
   Summary:
   Group: Pickup Ntaname: Upper East Side, Dropoff Ntaname: JFK Airport
   Total records: 1,234
   Trip Distance: avg 16.8 miles, median 15.2 miles
   Fare Amount: avg $52.30, median $51.20, range [$35.00 - $95.00]
   Tip Amount: avg $12.45, median $11.80, range [$0.00 - $45.00]
   
   Metadata:
    Records: 1,234
    avg_tip_amount: 12.45
    avg_tip_ratio: 0.238
```

### Find Weekend Patterns

```bash
python query_embeddings.py "weekend trip patterns" --top-k 10
```

**Finds:**
- Aggregations by day_of_week
- Saturday/Sunday pickup patterns
- Weekend vs weekday differences

### Find Expensive Trips

```bash
python query_embeddings.py "expensive long distance trips"
```

**Finds:**
- High fare routes
- Long distance aggregations
- Airport trips, outer borough routes

### Morning Rush Hour

```bash
python query_embeddings.py "morning rush hour pickups in Manhattan"
```

**Finds:**
- Hour = 7-9 AM aggregations
- Busy pickup neighborhoods
- Weekday morning patterns

### Find by Neighborhood

```bash
python query_embeddings.py "trips from East Harlem"
```

**Finds:**
- Aggregations where pickup_ntaname = "East Harlem"
- Popular destinations from East Harlem
- Average fares, distances, tips

## Advanced Usage

### Query with Filters

```bash
# Only search specific table
python query_embeddings.py "high tips" --table trips

# Get more results
python query_embeddings.py "airport trips" --top-k 20

# Filter by similarity threshold
python query_embeddings.py "expensive trips" --min-similarity 0.7
```

### Test Your Setup

```bash
# Test ClickHouse connection
python main.py --test-connection

# Should output:
# ✓ Connection successful!
```

## Real Query Examples

### Business Questions You Can Answer

**1. "What routes generate the most revenue?"**
```bash
python query_embeddings.py "routes with highest total fares"
```

**2. "When are tips highest?"**
```bash
python query_embeddings.py "time periods with high tipping"
```

**3. "Which neighborhoods have longest trips?"**
```bash
python query_embeddings.py "areas with long distance rides"
```

**4. "What are the patterns for credit card payments?"**
```bash
python query_embeddings.py "credit card payment patterns"
```

**5. "Find busy routes during weekdays"**
```bash
python query_embeddings.py "popular weekday routes high volume"
```

**6. "Show me airport pickup patterns"**
```bash
python query_embeddings.py "trips to JFK or LaGuardia airport"
```

**7. "What are the characteristics of nighttime trips?"**
```bash
python query_embeddings.py "late night and overnight rides"
```

## Understanding Results

### Similarity Score
- **0.9 - 1.0**: Extremely relevant
- **0.7 - 0.9**: Very relevant
- **0.5 - 0.7**: Somewhat relevant
- **< 0.5**: Less relevant

### Distance
- Lower distance = more similar
- Distance = 1 - Similarity

### Strategy Names
- `by_pickup_ntaname`: Grouped by pickup neighborhood
- `by_dropoff_ntaname`: Grouped by dropoff neighborhood
- `by_pickup_ntaname_and_dropoff_ntaname`: Routes (pickup → dropoff)
- `by_pickup_datetime_hour`: Hourly patterns
- `by_pickup_datetime_day_of_week`: Day of week patterns
- `by_pickup_datetime_month`: Monthly patterns

## Sample Workflow

### Day 1: Setup and Exploration
```bash
# 1. Test connection
python main.py --test-connection

# 2. See what strategies are available
python main.py trips --list-strategies

# 3. Estimate costs
python main.py trips --dry-run
```

### Day 2: Generate Embeddings
```bash
# Run the full pipeline
python main.py trips

# Wait ~1-2 minutes (depending on data size)
```

### Day 3: Start Querying
```bash
# Try various queries
python query_embeddings.py "high tips"
python query_embeddings.py "weekend patterns"
python query_embeddings.py "airport trips"
python query_embeddings.py "expensive routes"
```

### Day 4+: Build Applications
Use the embeddings in your own applications:
- Chatbot interface
- Analytics dashboard
- Recommendation system
- Anomaly detection

## Programmatic Usage

### In Python Code

```python
from clickhouse_client import get_client
from core import StorageManager, EmbeddingGenerator

# Setup
client = get_client()
storage = StorageManager(client)
embedding_gen = EmbeddingGenerator()

# Search
query = "routes with high tips"
query_embedding = embedding_gen.generate_embeddings([query])[0]

results = storage.search_similar(
    query_embedding=query_embedding,
    top_k=10,
    source_table='trips'
)

# Process results
for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Summary: {result['summary_text']}")
    print(f"Data: {result['metadata']}")
    print()
```

### Build a Simple Chatbot

```python
def chat_with_data(user_question: str):
    """Simple chatbot that queries embeddings."""
    client = get_client()
    storage = StorageManager(client)
    embedding_gen = EmbeddingGenerator()
    
    # Get relevant aggregations
    query_emb = embedding_gen.generate_embeddings([user_question])[0]
    results = storage.search_similar(query_emb, top_k=3, source_table='trips')
    
    # Format response
    response = f"Based on the data, here's what I found:\n\n"
    for i, result in enumerate(results, 1):
        response += f"{i}. {result['summary_text']}\n\n"
    
    return response

# Use it
print(chat_with_data("What routes have the highest tips?"))
```

## Tips for Better Results

### 1. Be Specific in Queries
❌ Bad: "tips"  
✅ Good: "routes with high tip amounts"

❌ Bad: "time"  
✅ Good: "morning rush hour patterns"

### 2. Use Natural Language
✅ "expensive trips"  
✅ "routes with long distances"  
✅ "weekend patterns in Manhattan"

### 3. Adjust top-k Based on Need
- **Quick answer**: `--top-k 3`
- **Exploration**: `--top-k 10`
- **Comprehensive**: `--top-k 20`

### 4. Filter When Needed
```bash
# Only very relevant results
python query_embeddings.py "query" --min-similarity 0.7

# Specific table
python query_embeddings.py "query" --table trips
```

## Troubleshooting

### No results found
- Try broader query terms
- Lower `--min-similarity` threshold
- Check if embeddings were generated: `SELECT COUNT(*) FROM aggregate_embeddings`

### Results not relevant
- Refine your query to be more specific
- Try different phrasing
- Check which strategies were used

### Slow queries
- Reduce `--top-k` value
- Add indexes to ClickHouse embeddings table

## Next Steps

1. ✅ Generate embeddings for your trips table
2. ✅ Try the example queries above
3. ✅ Experiment with your own questions
4. 🚀 Build applications using the embeddings!


