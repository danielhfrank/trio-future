import outcome
import trio

from trio_future.future import IntFuture

async def my_fn():
    await trio.sleep(1)
    return 7


def test_the_business():
    async def the_business():
        async with trio.open_nursery() as nursery:
            x = await IntFuture.run(my_fn, nursery)
            assert(x == outcome.Value(7))
    trio.run(the_business)
