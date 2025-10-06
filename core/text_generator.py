"""Convert aggregated data to natural language descriptions."""
from typing import Dict, Any, List
import re


class TextGenerator:
    """Generates natural language summaries from aggregated data."""
    
    def __init__(self):
        self.day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        self.month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December']
    
    def generate_summary(self, 
                        row: Dict[str, Any], 
                        group_by_cols: List[str],
                        numeric_cols: List[str]) -> str:
        """
        Generate natural language summary from an aggregated row.
        
        Args:
            row: Dictionary containing aggregated data
            group_by_cols: Columns used for grouping
            numeric_cols: Numeric columns that were aggregated
            
        Returns:
            Natural language summary text
        """
        parts = []
        
        # Part 1: Describe the grouping
        group_description = self._describe_grouping(row, group_by_cols)
        parts.append(group_description)
        
        # Part 2: Record count
        record_count = row.get('record_count', 0)
        parts.append(f"Total records: {record_count:,}")
        
        # Part 3: Summarize numeric columns
        for col in numeric_cols:
            col_summary = self._describe_numeric_column(row, col)
            if col_summary:
                parts.append(col_summary)
        
        # Join all parts with proper formatting
        return "\n".join(parts)
    
    def _describe_grouping(self, row: Dict[str, Any], group_cols: List[str]) -> str:
        """Create natural language description of the grouping."""
        descriptions = []
        
        for col in group_cols:
            value = row.get(col)
            if value is None or value == '':
                continue
            
            # Format special temporal values
            if col == 'hour_of_day':
                time_desc = self._describe_hour(value)
                descriptions.append(f"Time: {time_desc}")
            elif col == 'day_of_week':
                day_name = self.day_names[value - 1] if 1 <= value <= 7 else str(value)
                descriptions.append(f"Day: {day_name}")
            elif col == 'month':
                month_name = self.month_names[value - 1] if 1 <= value <= 12 else str(value)
                descriptions.append(f"Month: {month_name}")
            elif col == 'day_of_month':
                descriptions.append(f"Day of month: {value}")
            else:
                # Regular column
                human_name = self._humanize_column_name(col)
                descriptions.append(f"{human_name}: {value}")
        
        if descriptions:
            return "Group: " + ", ".join(descriptions)
        return "Overall aggregation"
    
    def _describe_hour(self, hour: int) -> str:
        """Convert hour to readable time description."""
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 21:
            period = "evening"
        else:
            period = "night"
        
        return f"{hour:02d}:00 ({period})"
    
    def _describe_numeric_column(self, row: Dict[str, Any], col: str) -> str:
        """Describe statistics for a numeric column."""
        avg = row.get(f'avg_{col}')
        min_val = row.get(f'min_{col}')
        max_val = row.get(f'max_{col}')
        median = row.get(f'median_{col}')
        stddev = row.get(f'stddev_{col}')
        
        # Skip if no data
        if avg is None:
            return ""
        
        human_name = self._humanize_column_name(col)
        
        # Detect if this is a monetary value
        is_money = any(term in col.lower() for term in ['amount', 'fare', 'price', 'cost', 'fee', 'tip', 'toll'])
        
        # Detect if this is a count
        is_count = 'count' in col.lower()
        
        # Build description
        parts = [f"{human_name}:"]
        
        if is_money:
            parts.append(f"avg ${avg:.2f}")
            if median is not None:
                parts.append(f"median ${median:.2f}")
            if min_val is not None and max_val is not None:
                parts.append(f"range [${min_val:.2f} - ${max_val:.2f}]")
        elif is_count:
            parts.append(f"avg {avg:.1f}")
            if median is not None:
                parts.append(f"median {median:.0f}")
            if min_val is not None and max_val is not None:
                parts.append(f"range [{int(min_val)} - {int(max_val)}]")
        else:
            # Generic numeric
            parts.append(f"avg {avg:.2f}")
            if median is not None:
                parts.append(f"median {median:.2f}")
            if min_val is not None and max_val is not None:
                parts.append(f"range [{min_val:.2f} - {max_val:.2f}]")
        
        # Add standard deviation if significant
        if stddev is not None and avg != 0:
            cv = stddev / avg  # Coefficient of variation
            if cv > 0.3:  # High variability
                parts.append(f"(high variability: σ={stddev:.2f})")
        
        return " ".join(parts)
    
    def _humanize_column_name(self, col_name: str) -> str:
        """
        Convert snake_case column name to readable text.
        
        Examples:
            'pickup_location' -> 'Pickup Location'
            'total_amount' -> 'Total Amount'
            'avg_trip_distance' -> 'Avg Trip Distance'
        """
        # Remove common prefixes
        for prefix in ['avg_', 'min_', 'max_', 'median_', 'stddev_', 'sum_', 'count_']:
            if col_name.startswith(prefix):
                col_name = col_name[len(prefix):]
                break
        
        # Convert to title case
        words = col_name.replace('_', ' ').split()
        
        # Capitalize each word, with special handling for acronyms
        capitalized = []
        for word in words:
            if word.isupper():
                capitalized.append(word)  # Keep acronyms as-is
            else:
                capitalized.append(word.capitalize())
        
        return ' '.join(capitalized)
    
    def create_embedding_id(self, row: Dict[str, Any], strategy_name: str) -> str:
        """
        Create a unique ID for this embedding.
        
        Args:
            row: Aggregated data row
            strategy_name: Name of the aggregation strategy
            
        Returns:
            Unique ID string
        """
        # Extract key values from the row (grouping columns)
        parts = [strategy_name]
        
        for key, value in row.items():
            # Skip aggregated statistics, only include grouping values
            if not any(key.startswith(prefix) for prefix in 
                      ['avg_', 'min_', 'max_', 'median_', 'stddev_', 'sum_', 'count_', 'record_']):
                if value is not None and value != '':
                    # Clean value for ID
                    clean_value = str(value).replace(' ', '_').replace('/', '_')
                    parts.append(clean_value)
        
        return "_".join(parts)


