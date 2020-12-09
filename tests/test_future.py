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


async def test_timeouts_inside_nursery():
    # In this test, we try to run a Future that we know will time out.
    # We demonstrate that code that tries to `await` the Future's result will never complete
    with trio.move_on_after(0.25):
        async with trio.open_nursery() as nursery:
            fut = Future.run(my_fn, nursery)
            await fut.outcome()
            assert False, "Should not get here"


async def test_timeouts_outside_nursery():
    # In this test, we try to run a Future that we know will time out.
    # We demonstrate that code that execution does not leave the nursery until the future completes;
    # Since the future times out, we never reach the code that is outside the nursery but inside the
    # cancel scope
    with trio.move_on_after(0.25):
        async with trio.open_nursery() as nursery:
            Future.run(my_fn, nursery)
        assert False, "Should not get here"


async def test_timeouts_outside_cancel_scope():
    # In this test, we try to run a Future that we know will time out.
    # Here, we show that it is possible to await the result of the Future if done outside of both
    # the cancel scope and the nursery. In this case, its result will be Error(Cancelled)
    with trio.move_on_after(0.25):
        async with trio.open_nursery() as nursery:
            fut = Future.run(my_fn, nursery)
        # Remember, we will jump right out from the nursery scope, since move_on_after will cancel.
        # Note however that `fut` is defined, since Future.run is synchronous
        assert False, "Should not get here"
    x = await fut.outcome()
    assert isinstance(x, Error)
    with pytest.raises(trio.Cancelled):
        x.unwrap()
