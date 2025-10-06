from typing import List, Dict, Any, Optional
import clickhouse_connect
from tqdm import tqdm

from core import (
    SchemaIntrospector,
    DimensionDetector,
    AggregationGenerator,
    TextGenerator,
    EmbeddingGenerator,
    StorageManager
)
from config import Config


class EmbeddingPipeline:
    def __init__(self, table_name: str, client: clickhouse_connect.driver.Client = None,
                 limit_strategies: Optional[List[str]] = None):
        self.table_name = table_name
        self.client = client or self._create_client()
        self.limit_strategies = limit_strategies
        
        self.schema_introspector = None
        self.dimension_detector = None
        self.aggregation_generator = None
        self.text_generator = None
        self.embedding_generator = None
        self.storage_manager = None
        
        self.schema = None
        self.dimensions = None
        self.strategies = None
    
    def _create_client(self) -> clickhouse_connect.driver.Client:
        return clickhouse_connect.get_client(
            host=Config.CLICKHOUSE_HOST,
            user=Config.CLICKHOUSE_USER,
            password=Config.CLICKHOUSE_PASSWORD,
            secure=Config.CLICKHOUSE_SECURE
        )
    
    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print(f"Embedding Pipeline for table: {self.table_name}")
        print(f"{'='*60}\n")
        
        print("Step 1: Initializing components...")
        self._initialize_components()
        
        print("\nStep 2: Introspecting table schema...")
        self.schema = self.schema_introspector.get_table_schema(self.table_name)
        print(f"✓ Found {len(self.schema)} columns")
        
        print("\nStep 3: Detecting dimensions...")
        self.dimensions = self.dimension_detector.detect(self.schema)
        print(self.dimensions)
        
        self.aggregation_generator = AggregationGenerator(self.table_name, self.dimensions)
        
        print("\nStep 4: Generating aggregation strategies...")
        all_strategies = self.aggregation_generator.generate_all_strategies()
        
        if self.limit_strategies:
            self.strategies = [s for s in all_strategies if s.name in self.limit_strategies]
            print(f"✓ Using {len(self.strategies)} strategies (filtered from {len(all_strategies)})")
        else:
            self.strategies = all_strategies
            print(f"✓ Generated {len(self.strategies)} strategies")
        
        if not self.strategies:
            print("⚠ No strategies to execute!")
            return {'error': 'No strategies available'}
        
        print("\nStep 5: Estimating work...")
        estimates = self._estimate_work()
        print(f"  Total aggregations: ~{estimates['total_aggregations']:,}")
        print(f"  Estimated cost: ${estimates['estimated_cost']:.4f}")
        print(f"  Estimated tokens: ~{estimates['estimated_tokens']:,}")
        
        if dry_run:
            print("\n[DRY RUN] Stopping here. Use run(dry_run=False) to execute.")
            return estimates
        
        if estimates['estimated_cost'] > 1.0:
            response = input(f"\n⚠ Estimated cost is ${estimates['estimated_cost']:.4f}. Continue? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled by user.")
                return {'cancelled': True}
        
        print("\nStep 6: Executing pipeline...")
        results = self._execute_pipeline()
        
        print("\nStep 7: Summary")
        self._print_summary(results)
        
        return results
    
    def _initialize_components(self):
        self.schema_introspector = SchemaIntrospector(self.client)
        self.dimension_detector = DimensionDetector()
        self.text_generator = TextGenerator()
        self.embedding_generator = EmbeddingGenerator()
        self.storage_manager = StorageManager(self.client)
        
        self.storage_manager.create_embeddings_table(
            embedding_dimension=self.embedding_generator.get_embedding_dimension()
        )
    
    def _estimate_work(self) -> Dict[str, Any]:
        total_aggs = 0
        
        for strategy in self.strategies[:3]:
            try:
                count = self.aggregation_generator.estimate_result_size(strategy, self.client)
                total_aggs += count
            except Exception as e:
                print(f"  Warning: Could not estimate {strategy.name}: {e}")
                total_aggs += 100
        
        if len(self.strategies) > 3:
            avg_per_strategy = total_aggs / 3
            total_aggs = int(avg_per_strategy * len(self.strategies))
        
        estimated_tokens = total_aggs * 100
        estimated_cost = self.embedding_generator.estimate_cost(total_aggs, 100)
        
        return {
            'total_aggregations': total_aggs,
            'estimated_tokens': estimated_tokens,
            'estimated_cost': estimated_cost,
            'num_strategies': len(self.strategies)
        }
    
    def _execute_pipeline(self) -> Dict[str, Any]:
        all_embeddings = []
        strategy_results = []
        
        for strategy in tqdm(self.strategies, desc="Processing strategies"):
            try:
                result = self._execute_strategy(strategy)
                strategy_results.append(result)
                all_embeddings.extend(result['embeddings'])
                
            except Exception as e:
                print(f"\n✗ Error in strategy '{strategy.name}': {e}")
                strategy_results.append({
                    'strategy': strategy.name,
                    'error': str(e),
                    'count': 0
                })
        
        embedding_stats = self.embedding_generator.get_stats()
        
        return {
            'table_name': self.table_name,
            'total_embeddings': len(all_embeddings),
            'strategies_executed': len([r for r in strategy_results if 'error' not in r]),
            'strategies_failed': len([r for r in strategy_results if 'error' in r]),
            'strategy_results': strategy_results,
            'embedding_stats': embedding_stats
        }
    
    def _execute_strategy(self, strategy) -> Dict[str, Any]:
        sql = self.aggregation_generator.generate_query(strategy)
        result = self.client.query(sql)
        
        if not result.result_rows:
            return {
                'strategy': strategy.name,
                'count': 0,
                'embeddings': []
            }
        
        rows = []
        for row in result.result_rows:
            row_dict = dict(zip(result.column_names, row))
            rows.append(row_dict)
        
        embeddings = []
        for row in rows:
            text = self.text_generator.generate_summary(
                row,
                strategy.get_select_cols(),
                self.dimensions.numeric
            )
            
            embeddings.append({
                'id': self.text_generator.create_embedding_id(row, strategy.name),
                'strategy_name': strategy.name,
                'text': text,
                'metadata': row
            })
        
        embeddings = self.embedding_generator.generate_embeddings_with_metadata(embeddings)
        self.storage_manager.insert_embeddings(embeddings, self.table_name)
        
        return {
            'strategy': strategy.name,
            'count': len(embeddings),
            'embeddings': embeddings
        }
    
    def _print_summary(self, results: Dict[str, Any]):
        print(f"\n{'='*60}")
        print("Pipeline Complete!")
        print(f"{'='*60}")
        print(f"Table: {results['table_name']}")
        print(f"Total embeddings generated: {results['total_embeddings']:,}")
        print(f"Strategies executed: {results['strategies_executed']}")
        print(f"Strategies failed: {results['strategies_failed']}")
        print(f"\nEmbedding API Stats:")
        stats = results['embedding_stats']
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Total tokens: {stats['total_tokens']:,}")
        print(f"  Total cost: ${stats['total_cost_usd']:.4f}")
        print(f"  Model: {stats['model']}")
        print(f"  Dimension: {stats['embedding_dimension']}")
        print(f"\n{'='*60}\n")
        
        if results['strategy_results']:
            print("\nPer-Strategy Results:")
            for sr in results['strategy_results']:
                if 'error' in sr:
                    print(f"  ✗ {sr['strategy']}: ERROR - {sr['error']}")
                else:
                    print(f"  ✓ {sr['strategy']}: {sr['count']} embeddings")
