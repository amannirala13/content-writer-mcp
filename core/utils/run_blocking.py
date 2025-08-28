import asyncio


def run_blocking(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        # loop is running; fire-and-forget or await elsewhere
        return asyncio.create_task(coro)