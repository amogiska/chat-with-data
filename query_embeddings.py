#!/usr/bin/env python3
"""
Query embeddings using natural language.

This script demonstrates how to search the generated embeddings
using semantic similarity.

Usage:
    python query_embeddings.py "routes with high tips"
    python query_embeddings.py "weekend patterns" --table trips --top-k 5
"""

import sys
import argparse
from typing import Optional

from config import Config
from clickhouse_client import get_client
from core import StorageManager, EmbeddingGenerator


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Query embeddings using natural language',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for routes with high tips
  python query_embeddings.py "routes with high tips"

  # Search with more results
  python query_embeddings.py "weekend patterns" --top-k 10

  # Search specific table
  python query_embeddings.py "expensive trips" --table trips
        """
    )
    
    parser.add_argument(
        'query',
        help='Natural language query'
    )
    
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of results to return (default: 5)'
    )
    
    parser.add_argument(
        '--table',
        type=str,
        help='Filter by source table name'
    )
    
    parser.add_argument(
        '--min-similarity',
        type=float,
        default=0.0,
        help='Minimum similarity threshold (0-1, default: 0.0)'
    )
    
    return parser.parse_args()


def format_metadata(metadata: dict) -> str:
    """Format metadata dictionary for display."""
    lines = []
    for key, value in metadata.items():
        if key == 'record_count':
            lines.append(f"    Records: {value:,}")
        elif isinstance(value, float):
            lines.append(f"    {key}: {value:.2f}")
        elif isinstance(value, int):
            lines.append(f"    {key}: {value:,}")
        else:
            lines.append(f"    {key}: {value}")
    return "\n".join(lines)


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Validate config
        Config.validate()
        
        print(f"\n{'='*60}")
        print(f"Searching embeddings for: '{args.query}'")
        print(f"{'='*60}\n")
        
        # Initialize components
        client = get_client()
        storage = StorageManager(client)
        embedding_gen = EmbeddingGenerator()
        
        # Generate query embedding
        print("Generating query embedding...")
        query_embedding = embedding_gen.generate_embeddings([args.query])[0]
        
        # Search for similar embeddings
        print(f"Searching for top {args.top_k} results...\n")
        results = storage.search_similar(
            query_embedding=query_embedding,
            top_k=args.top_k,
            source_table=args.table
        )
        
        # Filter by minimum similarity if specified
        if args.min_similarity > 0:
            results = [r for r in results if r['similarity'] >= args.min_similarity]
        
        # Display results
        if not results:
            print("No results found.")
            return 0
        
        print(f"Found {len(results)} results:\n")
        print("="*60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Similarity: {result['similarity']:.3f} | Distance: {result['distance']:.3f}")
            print(f"   Strategy: {result['strategy_name']}")
            print(f"   Source: {result['source_table']}")
            print(f"\n   Summary:")
            # Indent the summary text
            for line in result['summary_text'].split('\n'):
                print(f"   {line}")
            
            print(f"\n   Metadata:")
            print(format_metadata(result['metadata']))
            print("\n" + "-"*60)
        
        # Show query stats
        stats = embedding_gen.get_stats()
        print(f"\nQuery cost: ${stats['total_cost_usd']:.6f}")
        
        client.close()
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


