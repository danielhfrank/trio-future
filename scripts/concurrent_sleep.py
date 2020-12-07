import time

import trio
from trio_future.future import Future


async def echo(a: str) -> str:
    await trio.sleep(0.5)
    return a


async def main():
    start = time.time()
    hello = await echo("hello")
    world = await echo("world")
    elapsed = time.time() - start
    print(f"{hello} {world} executed in {elapsed}")
    async with trio.open_nursery() as nursery:
        # Naive implementation
        start = time.time()
        fut_1 = Future.run(lambda: echo("hello"), nursery)
        fut_2 = Future.run(lambda: echo("world"), nursery)
        hello = await fut_1.outcome()
        world = await fut_2.outcome()
        elapsed = time.time() - start
        print(f"{hello} {world} executed in {elapsed}")

        # join implementation
        start = time.time()
        fut_1 = Future.run(lambda: echo("hello"), nursery)
        fut_2 = Future.run(lambda: echo("world"), nursery)
        join_future = Future.join([fut_1, fut_2], nursery)
        outcome = await join_future.outcome()
        # TODO - need to re-wrap in an outcome as well.
        (hello, world) = outcome
        elapsed = time.time() - start
        print(f"{hello} {world} executed in {elapsed}")


if __name__ == "__main__":
    trio.run(main)
