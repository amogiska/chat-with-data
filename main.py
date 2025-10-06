#!/usr/bin/env python3
import sys
import argparse
from config import Config
from clickhouse_client import get_client, test_connection
from pipeline import EmbeddingPipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate aggregate embeddings from ClickHouse tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py trips
  python main.py trips --dry-run
  python main.py trips --strategies by_pickup_ntaname,by_route
  python main.py --test-connection
        """
    )
    
    parser.add_argument('table', nargs='?', help='ClickHouse table name')
    parser.add_argument('--dry-run', action='store_true', help='Preview without executing')
    parser.add_argument('--strategies', type=str, help='Comma-separated strategy names')
    parser.add_argument('--test-connection', action='store_true', help='Test connection')
    parser.add_argument('--list-strategies', action='store_true', help='List available strategies')
    
    return parser.parse_args()


def list_strategies(table_name: str):
    from core import SchemaIntrospector, DimensionDetector, AggregationGenerator
    
    print(f"\nDiscovering strategies for table: {table_name}\n")
    
    client = get_client()
    introspector = SchemaIntrospector(client)
    detector = DimensionDetector()
    
    schema = introspector.get_table_schema(table_name)
    dimensions = detector.detect(schema)
    
    print("Detected Dimensions:")
    print(f"  Categorical: {dimensions.categorical}")
    print(f"  Temporal: {dimensions.temporal}")
    print(f"  Numeric: {dimensions.numeric}")
    print(f"  Geospatial: {list(dimensions.geospatial.keys())}")
    
    generator = AggregationGenerator(table_name, dimensions)
    strategies = generator.generate_all_strategies()
    
    print(f"\nAvailable Strategies ({len(strategies)} total):\n")
    
    for strategy in strategies:
        print(f"  • {strategy.name}")
        print(f"    Description: {strategy.description}")
        print(f"    Groups by: {', '.join(strategy.group_by_cols)}")
        print()
    
    client.close()


def main():
    args = parse_args()
    
    if args.test_connection:
        print("Testing ClickHouse connection...")
        if test_connection():
            print("✓ Connection successful!")
            return 0
        else:
            print("✗ Connection failed!")
            return 1
    
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nSet required environment variables in .env or ~/.zshrc")
        return 1
    
    if not args.table:
        print("Error: table name required")
        print("Usage: python main.py <table_name> [options]")
        print("Run with --help for more information")
        return 1
    
    if args.list_strategies:
        list_strategies(args.table)
        return 0
    
    strategy_filter = None
    if args.strategies:
        strategy_filter = [s.strip() for s in args.strategies.split(',')]
    
    try:
        print("\n" + "="*60)
        print("Chat with Data - Aggregate Embeddings Pipeline")
        print("="*60)
        
        client = get_client()
        
        pipeline = EmbeddingPipeline(
            table_name=args.table,
            client=client,
            limit_strategies=strategy_filter
        )
        
        results = pipeline.run(dry_run=args.dry_run)
        
        client.close()
        
        if results.get('cancelled'):
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
