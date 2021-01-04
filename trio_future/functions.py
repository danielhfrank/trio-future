from typing import List, Callable, Awaitable, Any

import outcome
import trio

from .future import Future


def run(nursery: trio.Nursery, async_fn: Callable[..., Awaitable[Any]], *args) -> Future:
    """Run an async function and capture its result in a Future. This is the main entrypoint for trio-future.

    Note that this is a synchronous function; it will immediately a :class:`Future` object. This object
    can be used to access the return value of ``async_fn``. However, the function will *not* have begun execution.
    Under the hood, we will pass the function to ``nursery.start_soon``; its execution will begin when we
    next defer to the scheduler.

    :param nursery: Nursery in which to run the function
    :type nursery: trio.Nursery
    :param async_fn: A trio-flavored async function to run. Positional arguments may be passed as trailing args, keyword arguments must use ``functools.partial`` or similar.
    :type async_fn: Callable[..., Awaitable[Any]]
    :return: A Future object allowing access to the return value of ``async_fn``.
    :rtype: Future
    """
    # Set buffer size to 1 so that producer can send a single result
    # witout blocking on a receiver.
    send_chan, recv_chan = trio.open_memory_channel(1)

    async def producer(*args):
        return_val = await outcome.acapture(async_fn, *args)
        # Shield sending the result from parent cancellation. This allows the Future to store
        # the outcome of the operation, namely that it was cancelled.
        # Note that the channel is buffered and only sent from here, so it should not block.
        with trio.CancelScope(shield=True):
            async with send_chan:
                await send_chan.send(return_val)

    nursery.start_soon(producer, *args)

    return Future(recv_chan, nursery)


def gather(nursery: trio.Nursery, futures: List[Future]) -> Future:
    """Concurrently run multiple Futures.

    This function will allow the provided Futures to run concurrently, and gather their results
    into a single :class:`Future` containing the results of all the inputs.
    That is, if each input Future contained an ``int``, then the returned Future will contain a ``List[int]``. In practice,
    the types need not be homogenous. The list enclosed in the returned Future will have the same ordering as the input list.

    If any Futures throw an exception, then the output Future will contain those exceptions, wrapped in a ``trio.MultiError``.

    :param nursery: Nursery that manages the concurrent execution of the provided futures
    :type nursery: trio.Nursery
    :param futures: Futures to run
    :type futures: List[Future]
    :return: A Future containing the results of all the provided futures.
    :rtype: Future
    """
    result_list = [None] * len(futures)
    parent_send_chan, parent_recv_chan = trio.open_memory_channel(0)
    child_send_chan, child_recv_chan = trio.open_memory_channel(0)

    async def producer():
        async with child_send_chan:
            for i in range(len(futures)):
                nursery.start_soon(child_producer, i, child_send_chan.clone())

    async def child_producer(i: int, out_chan):
        async with futures[i].result_chan:
            return_val = await futures[i].result_chan.receive()
            result_list[i] = return_val
            async with out_chan:
                await out_chan.send(i)

    async def receiver():
        async with child_recv_chan:
            async for i in child_recv_chan:
                # Just consume all results from the channel until exhausted
                pass
        # And then wrap up the result and push it to the parent channel
        errors = [e.error for e in result_list if isinstance(e, outcome.Error)]
        if len(errors) > 0:
            result = outcome.Error(trio.MultiError(errors))
        else:
            result = outcome.Value([o.unwrap() for o in result_list])
        async with parent_send_chan:
            await parent_send_chan.send(result)

    # Start parent producer, which will in turn start all children
    # (doing this inside the nursery because it needs to act async)
    nursery.start_soon(producer)
    nursery.start_soon(receiver)
    return Future(parent_recv_chan, nursery)
