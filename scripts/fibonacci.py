import sys

import trio
from trio_future import gather, run


async def fib(n: int) -> int:
    if n < 0:
        raise ValueError("boom")
    elif n in {0, 1}:
        return 1
    else:
        async with trio.open_nursery() as nursery:
            results = await gather(
                nursery,
                [run(nursery, fib, n-1), run(nursery, fib, n-2)],
            ).get()
            return sum(results)


if __name__ == "__main__":
    n = int(sys.argv[1])
    result = trio.run(fib, n)
    print(result)
