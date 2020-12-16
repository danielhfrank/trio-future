import time

import trio
from trio_future.future import Future


async def echo(a: str) -> str:
    await trio.sleep(0.5)
    return a


async def main():
    # Sequential blocking calls
    start = time.time()
    hello = await echo("hello")
    world = await echo("world")
    elapsed = time.time() - start
    print(f"{hello} {world} executed in {elapsed}")
    async with trio.open_nursery() as nursery:
        # Naive use of futures, still allows for concurrent execution
        start = time.time()
        fut_1 = Future.run(nursery, echo, "hello")
        fut_2 = Future.run(nursery, echo, "world")
        hello = await fut_1.outcome()
        world = await fut_2.outcome()
        elapsed = time.time() - start
        print(f"{hello} {world} executed in {elapsed}")

        # Using future.join
        start = time.time()
        fut_1 = Future.run(nursery, echo, "hello")
        fut_2 = Future.run(nursery, echo, "world")
        join_future = Future.join(nursery, [fut_1, fut_2])
        outcome = await join_future.outcome()
        elapsed = time.time() - start
        print(f"{outcome} executed in {elapsed}")

        # Ok now let's try doing something bad
        fut = Future.run(nursery, echo, 'uh oh')
        print('leaving')
    print('left')
    await fut.outcome()
    try:
        await fut.outcome()
    except Exception:
        print('gotcha')


if __name__ == "__main__":
    trio.run(main)
