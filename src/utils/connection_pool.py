"""Connection pool manager for efficient HTTP connections."""

import logging
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """
    Manages HTTP connection pools for efficient API communication.

    Benefits:
    - Reuses TCP connections (faster, less overhead)
    - Automatic retries with exponential backoff
    - Connection pooling reduces latency
    - Thread-safe
    """

    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
        max_retries: int = 3,
        backoff_factor: float = 0.3
    ):
        """
        Initialize connection pool manager.

        Args:
            pool_connections: Number of connection pools to cache
            pool_maxsize: Max connections per pool
            max_retries: Max retry attempts
            backoff_factor: Backoff multiplier for retries
        """
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )

        # Create HTTP adapter with connection pooling
        self.adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )

        logger.info(
            f"Connection pool initialized: {pool_connections} pools, "
            f"{pool_maxsize} connections/pool, {max_retries} retries"
        )

    def get_session(self) -> requests.Session:
        """
        Get a configured requests session with connection pooling.

        Returns:
            Configured requests.Session instance
        """
        session = requests.Session()

        # Mount adapter for both HTTP and HTTPS
        session.mount("http://", self.adapter)
        session.mount("https://", self.adapter)

        return session


# Global pool manager instance
_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """Get singleton connection pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager


def get_optimized_session() -> requests.Session:
    """
    Get an optimized requests session with connection pooling.

    Usage:
        session = get_optimized_session()
        response = session.get("https://api.example.com/endpoint")
    """
    return get_pool_manager().get_session()
