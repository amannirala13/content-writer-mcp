import asyncio
import inspect


def run_blocking(coro_or_func, *args, **kwargs):
    """
    Run a coroutine or async function in a blocking manner.

    Args:
        coro_or_func: Either a coroutine object or an async function
        *args, **kwargs: Arguments to pass to the function if coro_or_func is a function

    Returns:
        The result of the coroutine execution
    """
    # If it's a function, call it with the provided arguments
    if inspect.iscoroutinefunction(coro_or_func):
        coro = coro_or_func(*args, **kwargs)
    elif inspect.iscoroutine(coro_or_func):
        coro = coro_or_func
    else:
        # It's a regular function, just call it normally
        return coro_or_func(*args, **kwargs)

    try:
        # Check if there's already a running event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(coro)
    else:
        # There's already a running loop, we need to handle this differently
        # This is more complex and depends on your specific use case
        import concurrent.futures
        import threading

        # Create a new event loop in a separate thread
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()