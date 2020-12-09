from __future__ import annotations

from typing import List

from dataclasses import dataclass

import trio
import outcome


@dataclass
class Future:

    # TODO we can type this!
    result_chan: trio.abc.ReceiveChannel
    nursery: trio.Nursery  # TODO not sure if we need this but feels like good practice

    @staticmethod
    def run(async_fn, nursery: trio.Nursery) -> Future:
        # Set buffer size to 1 so that producer can send a single result
        # witout blocking on a receiver.
        send_chan, recv_chan = trio.open_memory_channel(1)

        async def producer():
            return_val = await outcome.acapture(async_fn)
            # Shield sending the result from parent cancellation. This allows the Future to store
            # the outcome of the operation, namely that it was cancelled.
            # Note that the channel is buffered and only sent from here, so it should not block.
            with trio.CancelScope(shield=True):
                async with send_chan:
                    await send_chan.send(return_val)

        nursery.start_soon(producer)

        return Future(recv_chan, nursery)

    async def get(self):
        future_outcome = await self.outcome()
        return future_outcome.unwrap()

    async def outcome(self) -> outcome.Outcome:
        async with self.result_chan:
            return await self.result_chan.receive()

    @staticmethod
    def join(futures: List[Future], nursery: trio.Nursery) -> Future:
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
