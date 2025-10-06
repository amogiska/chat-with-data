"""Dynamic SQL aggregation query generation."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .dimension_detector import Dimensions
from config import StrategyConfig, Config


@dataclass
class AggregationStrategy:
    """Defines a single aggregation strategy."""
    name: str
    description: str
    group_by_cols: List[str]
    group_by_exprs: Optional[List[str]] = None  # Custom expressions (e.g., toHour(datetime))
    filters: Optional[str] = None
    
    def get_group_by_clause(self) -> str:
        """Get the GROUP BY clause."""
        if self.group_by_exprs:
            return ", ".join(self.group_by_exprs)
        return ", ".join(self.group_by_cols)
    
    def get_select_cols(self) -> List[str]:
        """Get the column names for SELECT (after aggregation)."""
        if self.group_by_exprs:
            # Extract alias from expressions like "toHour(pickup_datetime) as hour"
            cols = []
            for expr in self.group_by_exprs:
                if ' as ' in expr.lower():
                    alias = expr.lower().split(' as ')[-1].strip()
                    cols.append(alias)
                else:
                    cols.append(expr)
            return cols
        return self.group_by_cols


class AggregationGenerator:
    """Generates SQL queries for different aggregation strategies."""
    
    def __init__(self, table_name: str, dimensions: Dimensions):
        self.table_name = table_name
        self.dimensions = dimensions
    
    def generate_all_strategies(self) -> List[AggregationStrategy]:
        """Generate all enabled aggregation strategies."""
        strategies = []
        
        if StrategyConfig.ENABLE_SINGLE_DIMENSION:
            strategies.extend(self._generate_single_dimension_strategies())
        
        if StrategyConfig.ENABLE_DIMENSION_PAIRS:
            strategies.extend(self._generate_dimension_pair_strategies())
        
        if StrategyConfig.ENABLE_TEMPORAL_PATTERNS:
            strategies.extend(self._generate_temporal_strategies())
        
        return strategies
    
    def _generate_single_dimension_strategies(self) -> List[AggregationStrategy]:
        """Generate strategies for single categorical dimensions."""
        strategies = []
        
        for col in self.dimensions.categorical:
            strategies.append(AggregationStrategy(
                name=f"by_{col}",
                description=f"Aggregated by {col}",
                group_by_cols=[col],
                filters=f"{col} != '' AND {col} IS NOT NULL"
            ))
        
        return strategies
    
    def _generate_dimension_pair_strategies(self) -> List[AggregationStrategy]:
        """Generate strategies for pairs of categorical dimensions."""
        strategies = []
        cat_cols = self.dimensions.categorical
        
        # Limit number of pairs to avoid explosion
        pair_count = 0
        max_pairs = Config.MAX_DIMENSION_PAIRS
        
        for i, col1 in enumerate(cat_cols):
            for col2 in cat_cols[i+1:]:
                if pair_count >= max_pairs:
                    break
                
                strategies.append(AggregationStrategy(
                    name=f"by_{col1}_and_{col2}",
                    description=f"Aggregated by {col1} and {col2}",
                    group_by_cols=[col1, col2],
                    filters=f"{col1} != '' AND {col1} IS NOT NULL AND {col2} != '' AND {col2} IS NOT NULL"
                ))
                pair_count += 1
            
            if pair_count >= max_pairs:
                break
        
        return strategies
    
    def _generate_temporal_strategies(self) -> List[AggregationStrategy]:
        """Generate strategies for temporal patterns."""
        strategies = []
        
        for time_col in self.dimensions.temporal:
            for granularity in StrategyConfig.TEMPORAL_GRANULARITIES:
                strategy = self._create_temporal_strategy(time_col, granularity)
                if strategy:
                    strategies.append(strategy)
        
        return strategies
    
    def _create_temporal_strategy(self, time_col: str, granularity: str) -> Optional[AggregationStrategy]:
        """Create a temporal aggregation strategy."""
        granularity_map = {
            'hour': ('toHour', 'hour_of_day'),
            'day_of_week': ('toDayOfWeek', 'day_of_week'),
            'day_of_month': ('toDayOfMonth', 'day_of_month'),
            'month': ('toMonth', 'month'),
        }
        
        if granularity not in granularity_map:
            return None
        
        func, alias = granularity_map[granularity]
        
        return AggregationStrategy(
            name=f"by_{time_col}_{granularity}",
            description=f"Aggregated by {granularity} from {time_col}",
            group_by_cols=[alias],
            group_by_exprs=[f"{func}({time_col}) as {alias}"]
        )
    
    def generate_query(self, strategy: AggregationStrategy) -> str:
        """
        Generate the full SQL query for an aggregation strategy.
        
        Args:
            strategy: The aggregation strategy to generate SQL for
            
        Returns:
            SQL query string
        """
        # Build SELECT clause
        select_parts = []
        
        # Add grouping columns/expressions
        if strategy.group_by_exprs:
            select_parts.extend(strategy.group_by_exprs)
        else:
            select_parts.extend(strategy.group_by_cols)
        
        # Add aggregations for numeric columns
        select_parts.append("COUNT(*) as record_count")
        
        for num_col in self.dimensions.numeric:
            select_parts.extend([
                f"AVG({num_col}) as avg_{num_col}",
                f"MIN({num_col}) as min_{num_col}",
                f"MAX({num_col}) as max_{num_col}",
                f"quantile(0.5)({num_col}) as median_{num_col}",
                f"stddevPop({num_col}) as stddev_{num_col}"
            ])
        
        select_clause = ",\n    ".join(select_parts)
        
        # Build WHERE clause
        where_clause = f"WHERE {strategy.filters}" if strategy.filters else ""
        
        # Build GROUP BY clause
        group_clause = strategy.get_group_by_clause()
        
        # Build HAVING clause
        having_clause = f"HAVING record_count >= {Config.MIN_RECORDS_PER_GROUP}"
        
        # Assemble query
        query = f"""
SELECT 
    {select_clause}
FROM {self.table_name}
{where_clause}
GROUP BY {group_clause}
{having_clause}
ORDER BY record_count DESC
""".strip()
        
        return query
    
    def estimate_result_size(self, strategy: AggregationStrategy, client) -> int:
        """
        Estimate how many result rows a strategy will produce.
        
        Args:
            strategy: The aggregation strategy
            client: ClickHouse client
            
        Returns:
            Estimated number of result rows
        """
        if strategy.group_by_exprs:
            group_cols = ", ".join(strategy.group_by_exprs)
        else:
            group_cols = ", ".join(strategy.group_by_cols)
        
        where_clause = f"WHERE {strategy.filters}" if strategy.filters else ""
        
        query = f"""
        SELECT COUNT(DISTINCT ({group_cols}))
        FROM {self.table_name}
        {where_clause}
        """
        
        try:
            result = client.query(query)
            return result.result_rows[0][0]
        except Exception:
            # If estimation fails, return a conservative estimate
            return 100


