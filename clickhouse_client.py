"""ClickHouse client utilities."""
import clickhouse_connect
from config import Config


def get_client() -> clickhouse_connect.driver.Client:
    """
    Get a ClickHouse client using configuration.
    
    Returns:
        ClickHouse client instance
    """
    return clickhouse_connect.get_client(
        host=Config.CLICKHOUSE_HOST,
        user=Config.CLICKHOUSE_USER,
        password=Config.CLICKHOUSE_PASSWORD,
        secure=Config.CLICKHOUSE_SECURE
    )


def test_connection() -> bool:
    """
    Test the ClickHouse connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = get_client()
        result = client.query("SELECT 1").result_set[0][0]
        client.close()
        return result == 1
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False