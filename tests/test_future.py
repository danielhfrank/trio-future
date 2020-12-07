from outcome import Value, Error
import pytest
import trio

from trio_future.future import Future


async def my_fn():
    await trio.sleep(3)
    return 7


async def throws_error():
    await trio.sleep(1)
    raise RuntimeError("Boom")


async def test_the_future():
    async with trio.open_nursery() as nursery:
        fut = Future.run(my_fn, nursery)
        func_outcome = await fut.outcome()
        assert func_outcome == Value(7)


async def test_throws_error():
    async with trio.open_nursery() as nursery:
        fut = Future.run(throws_error, nursery)
        # note that if we had awaited the function, this would just raise an exception
        func_outcome = await fut.outcome()
        assert isinstance(func_outcome, Error)
        with pytest.raises(RuntimeError):
            func_outcome.unwrap()


async def test_join():
    async with trio.open_nursery() as nursery:
        future_list = [Future.run(my_fn, nursery) for _ in range(10)]
        joined_future = Future.join(future_list, nursery)
        assert await joined_future.outcome() == Value([7] * 10)


async def test_join_with_errors():
    async with trio.open_nursery() as nursery:
        future_list = [Future.run(my_fn, nursery), Future.run(throws_error, nursery)]
        joined_future = Future.join(future_list, nursery)
        outcome = await joined_future.outcome()
        assert isinstance(outcome, Error)
        with pytest.raises(RuntimeError):
            outcome.unwrap()
