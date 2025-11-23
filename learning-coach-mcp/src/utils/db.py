"""Database utilities for Supabase."""

from typing import Optional
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


def get_supabase_client(url: str, key: str) -> Client:
    """
    Create and return a Supabase client.

    Args:
        url: Supabase project URL
        key: Supabase API key

    Returns:
        Supabase client instance
    """
    try:
        client = create_client(url, key)
        logger.debug("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        raise


async def check_db_connection(client: Client) -> bool:
    """
    Check if database connection is working.

    Args:
        client: Supabase client

    Returns:
        True if connection successful, False otherwise
    """
    try:
        # Try a simple query
        result = client.table("users").select("id").limit(1).execute()
        logger.debug("Database connection check successful")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
