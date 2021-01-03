from outcome import Value, Error
import pytest
import trio

# from trio_future.future import Future
from trio_future import run, gather


async def my_fn():
    await trio.sleep(3)
    return 7


async def throws_error():
    await trio.sleep(1)
    raise RuntimeError("Boom")


async def test_the_future():
    async with trio.open_nursery() as nursery:
        fut = run(nursery, my_fn)
        func_outcome = await fut.outcome()
        assert func_outcome == Value(7)


async def test_throws_error():
    async with trio.open_nursery() as nursery:
        fut = run(nursery, throws_error)
        # note that if we had awaited the function, this would just raise an exception
        func_outcome = await fut.outcome()
        assert isinstance(func_outcome, Error)
        with pytest.raises(RuntimeError):
            func_outcome.unwrap()


async def test_gather():
    async with trio.open_nursery() as nursery:
        future_list = [run(nursery, my_fn) for _ in range(10)]
        joined_future = gather(nursery, future_list)
        assert await joined_future.outcome() == Value([7] * 10)


async def test_gather_with_errors():
    async with trio.open_nursery() as nursery:
        future_list = [run(nursery, my_fn), run(nursery, throws_error)]
        joined_future = gather(nursery, future_list)
        outcome = await joined_future.outcome()
        assert isinstance(outcome, Error)
        with pytest.raises(RuntimeError):
            outcome.unwrap()


@pytest.mark.xfail(reason="Nondeterministic failure", raises=trio.BrokenResourceError)
async def test_timeouts_inside_nursery():
    # In this test, we try to run a Future that we know will time out.
    # We demonstrate that code that tries to `await` the Future's result will never complete
    with trio.move_on_after(0.25):
        async with trio.open_nursery() as nursery:
            fut = run(nursery, my_fn)
            await fut.outcome()
            assert False, "Should not get here"


async def test_timeouts_outside_nursery():
    # In this test, we try to run a Future that we know will time out.
    # We demonstrate that code that execution does not leave the nursery until the future completes;
    # Since the future times out, we never reach the code that is outside the nursery but inside the
    # cancel scope
    with trio.move_on_after(0.25):
        async with trio.open_nursery() as nursery:
            run(nursery, my_fn)
        assert False, "Should not get here"


async def test_timeouts_outside_cancel_scope():
    # In this test, we try to run a Future that we know will time out.
    # Here, we show that it is possible to await the result of the Future if done outside of both
    # the cancel scope and the nursery. In this case, its result will be Error(Cancelled)
    with trio.move_on_after(0.25):
        async with trio.open_nursery() as nursery:
            fut = run(nursery, my_fn)
        # Remember, we will jump right out from the nursery scope, since move_on_after will cancel.
        # Note however that `fut` is defined, since run is synchronous
        assert False, "Should not get here"
    x = await fut.outcome()
    assert isinstance(x, Error)
    with pytest.raises(trio.Cancelled):
        x.unwrap()


async def echo(n: int) -> int:
    await trio.sleep(1)
    return n


async def test_fn_args():
    async with trio.open_nursery() as nursery:
        fut = run(nursery, echo, 2)
        result = await fut.get()
        assert result == 2


async def test_outcome_twice():
    async with trio.open_nursery() as nursery:
        fut = run(nursery, echo, 2)
        await fut.outcome()
        with pytest.raises(RuntimeError):
            await fut.outcome()
