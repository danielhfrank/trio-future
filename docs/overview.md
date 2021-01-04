# trio-future

## Overview

`trio-future` allows you to execute execute trio asynchronous functions concurrently, while retaining references to their return values. It's an altnerative to using trio channels to communicate results between tasks that feels more like programming with normal functions.

Consider an example with this simple echo function:
```python
async def echo(a: str) -> str:
    await trio.sleep(0.5)
    return a
```
We can call our function and get its result back later when we are ready:
```python
async with trio.open_nursery() as nursery:
    # Call trio_future.run to synchronously get back a Future
    future = trio_future.run(nursery, echo, "hello")
    # When we call `await` and yield to scheduler, our function begins executing
    await trio.sleep(0.1)
    # We can `await` the function when we are ready
    hello = await future.get() 
    # hello == "hello"
```
A common use-case is to run several tasks concurrently and wait for them all to complete. `trio-future` has a `gather` function like `asyncio.gather` to do this:
```python
async with trio.open_nursery() as nursery:
    fut_1 = run(nursery, echo, "hello")
    fut_2 = run(nursery, echo, "world")
    # Call `gather` to package the two Futures into a single Future object.
    # Note that this is again a synchronous function.
    joined_future = gather(nursery, [fut_1, fut_2])
    # Again, when we `await` the result, we yield to the scheduler. This time, both
    # of our futures will execute concurrently.
    hello_world = await join_future.get()
    # hello_world = ["hello", "world"]
```
