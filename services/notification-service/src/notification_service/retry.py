"""Retry mechanism with exponential backoff."""

import asyncio
from typing import Callable, Any, Optional, Tuple

from shared.utils.logger import setup_logger

logger = setup_logger(__name__)


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    *args,
    **kwargs,
) -> Tuple[bool, Any, Optional[str]]:
    """
    Retry function with exponential backoff.

    Args:
        func: Async function to retry (should return tuple of (success, result, error))
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Tuple of (success, result, error_message)
    """
    last_error = None
    last_result = None

    for attempt in range(1, max_retries + 1):
        try:
            success, result, error = await func(*args, **kwargs)
            if success:
                if attempt > 1:
                    logger.info(f"Retry attempt {attempt} succeeded")
                return True, result, None
            else:
                last_error = error
                last_result = result
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {last_error}")

                if attempt < max_retries:
                    # Calculate exponential backoff delay
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed. Last error: {last_error}")

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt}/{max_retries} raised exception: {last_error}")

            if attempt < max_retries:
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed. Last error: {last_error}")

    return False, last_result, last_error

