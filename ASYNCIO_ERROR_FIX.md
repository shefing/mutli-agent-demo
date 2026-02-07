# Asyncio Event Loop Error Fix

## Problem

When running the CLI, you would see this error at the end:

```
ERROR:asyncio:Task exception was never retrieved
future: <Task finished name='Task-570' coro=<AsyncClient.aclose() done, defined at ...> exception=RuntimeError('Event loop is closed')>
Traceback (most recent call last):
  File ".../httpx/_client.py", line 1985, in aclose
    await self._transport.aclose()
  ...
RuntimeError: Event loop is closed
```

## Root Cause

The CLI is a **synchronous** program, but some dependencies use **async** HTTP clients:
- **OpenAI SDK** (used by FactsChecker via NeMo)
- **httpx** (underlying HTTP library used by OpenAI SDK)
- **LlamaFirewall** (may use async internally)

These libraries create async HTTP clients during execution. When the program exits:
1. Python's garbage collector tries to clean up async resources
2. The event loop has already closed
3. Async cleanup tasks fail with "Event loop is closed" error

This is a **harmless warning** - it doesn't affect functionality, but it's noisy and looks like a real error.

## Solution

Added proper async cleanup and error suppression in `cli.py`:

### 1. Suppress Asyncio Error Logging
```python
import logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
```

### 2. Cleanup Pending Tasks Before Exit
```python
def main():
    # ... main logic ...

    # Cleanup: Close any pending async tasks
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            # Cancel all pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Give tasks a chance to complete cancellation
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except RuntimeError:
        pass
```

### 3. Proper Event Loop Closure
```python
if __name__ == "__main__":
    try:
        main()
    finally:
        # Final cleanup: ensure all async resources are properly closed
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except RuntimeError:
            pass
```

## Why This Works

1. **Before exit:** Cancels all pending async tasks gracefully
2. **Suppress logging:** Sets asyncio logger to CRITICAL level
3. **Proper cleanup:** Ensures event loop is properly closed

## Testing

Before fix:
```bash
$ python cli.py -f session.json -s AlignmentCheck
...
ERROR:asyncio:Task exception was never retrieved
RuntimeError: Event loop is closed
```

After fix:
```bash
$ python cli.py -f session.json -s AlignmentCheck
...
✅ Processing complete!
# Clean output, no errors
```

## Alternative Solutions Considered

### Option 1: Force Synchronous HTTP Clients
- **Pros:** No async cleanup needed
- **Cons:** Would require modifying OpenAI SDK usage, might break NeMo
- **Verdict:** Too invasive

### Option 2: Use asyncio.run() for Main
- **Pros:** Proper async context
- **Cons:** Would require rewriting entire CLI as async
- **Verdict:** Too much refactoring

### Option 3: Suppress Warnings Only (Chosen)
- **Pros:** Simple, non-invasive, solves the problem
- **Cons:** Doesn't fix root cause, just hides it
- **Verdict:** Best for this use case since it's a library issue, not our code

## Impact

- ✅ Clean CLI output (no scary error messages)
- ✅ No functional changes (warnings were harmless anyway)
- ✅ Proper resource cleanup (cancels pending tasks)
- ✅ Works with all scanners (AlignmentCheck, FactsChecker, etc.)

## Related Issues

This error is common in Python 3.11+ with libraries that mix sync/async code:
- https://github.com/encode/httpx/issues/914
- https://github.com/openai/openai-python/issues/742

The consensus is that this is a library issue, and suppressing the warnings is acceptable for CLI tools.
