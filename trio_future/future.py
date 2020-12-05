import trio
import outcome


class IntFuture:
    @staticmethod
    async def run(async_fn, nursery: trio.Nursery) -> outcome.Outcome:
        send_chan, recv_chan = trio.open_memory_channel(0)

        async def producer():
            return_val = await async_fn()
            async with send_chan:
                await send_chan.send(return_val)

        nursery.start_soon(producer)
        async with recv_chan:
            # TODO sketchy anext, no idea if this will work
            x = await recv_chan.__anext__()
            return outcome.Value(x)
