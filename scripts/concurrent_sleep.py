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
        fut_1 = Future.run(lambda: echo("hello"), nursery)
        fut_2 = Future.run(lambda: echo("world"), nursery)
        hello = await fut_1.outcome()
        world = await fut_2.outcome()
        elapsed = time.time() - start
        print(f"{hello} {world} executed in {elapsed}")

        # Using future.join
        start = time.time()
        fut_1 = Future.run(lambda: echo("hello"), nursery)
        fut_2 = Future.run(lambda: echo("world"), nursery)
        join_future = Future.join([fut_1, fut_2], nursery)
        outcome = await join_future.outcome()
        elapsed = time.time() - start
        print(f"{outcome} executed in {elapsed}")

        # Ok now let's try doing something bad
        fut = Future.run(lambda: echo('uh oh'), nursery)
        print('leaving')
    print('left')
    await fut.outcome()
    await fut.outcome()


if __name__ == "__main__":
    trio.run(main)
