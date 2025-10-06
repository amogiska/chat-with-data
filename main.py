#!/usr/bin/env python3
"""
Chat with Data - Aggregate Embeddings Pipeline

This tool generates embeddings from table aggregations and stores them in ClickHouse.
It automatically discovers table schemas, creates meaningful aggregations, converts them
to natural language, generates embeddings, and stores them for semantic search.

Usage:
    python main.py <table_name> [options]
    python main.py trips --dry-run
    python main.py trips --strategies by_pickup_ntaname,by_route
"""

import sys
import argparse
from typing import Optional

from config import Config
from clickhouse_client import get_client, test_connection
from pipeline import EmbeddingPipeline


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate aggregate embeddings from ClickHouse tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline on 'trips' table
  python main.py trips

  # Dry run to see what would be done
  python main.py trips --dry-run

  # Run specific strategies only
  python main.py trips --strategies by_pickup_ntaname,by_route

  # Test connection
  python main.py --test-connection
        """
    )
    
    parser.add_argument(
        'table',
        nargs='?',
        help='Name of the ClickHouse table to process'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    
    parser.add_argument(
        '--strategies',
        type=str,
        help='Comma-separated list of strategy names to run (runs all if not specified)'
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test ClickHouse connection and exit'
    )
    
    parser.add_argument(
        '--list-strategies',
        action='store_true',
        help='List available strategies for the table and exit'
    )
    
    return parser.parse_args()


def list_strategies(table_name: str):
    """List available aggregation strategies for a table."""
    from core import SchemaIntrospector, DimensionDetector, AggregationGenerator
    
    print(f"\nDiscovering strategies for table: {table_name}\n")
    
    client = get_client()
    
    # Introspect and detect
    introspector = SchemaIntrospector(client)
    detector = DimensionDetector()
    
    schema = introspector.get_table_schema(table_name)
    dimensions = detector.detect(schema)
    
    print("Detected Dimensions:")
    print(f"  Categorical: {dimensions.categorical}")
    print(f"  Temporal: {dimensions.temporal}")
    print(f"  Numeric: {dimensions.numeric}")
    print(f"  Geospatial: {list(dimensions.geospatial.keys())}")
    
    # Generate strategies
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
    """Main entry point."""
    args = parse_args()
    
    # Test connection if requested
    if args.test_connection:
        print("Testing ClickHouse connection...")
        if test_connection():
            print("✓ Connection successful!")
            return 0
        else:
            print("✗ Connection failed!")
            return 1
    
    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease set required environment variables in .env file.")
        print("See .env.example for reference.")
        return 1
    
    # Require table name
    if not args.table:
        print("Error: table name is required")
        print("Usage: python main.py <table_name> [options]")
        print("Run with --help for more information")
        return 1
    
    # List strategies if requested
    if args.list_strategies:
        list_strategies(args.table)
        return 0
    
    # Parse strategies filter
    strategy_filter = None
    if args.strategies:
        strategy_filter = [s.strip() for s in args.strategies.split(',')]
    
    # Run the pipeline
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