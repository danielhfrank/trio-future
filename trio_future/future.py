from __future__ import annotations

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
        send_chan, recv_chan = trio.open_memory_channel(0)

        async def producer():
            return_val = await outcome.acapture(async_fn)
            async with send_chan:
                await send_chan.send(return_val)

        nursery.start_soon(producer)

        return Future(recv_chan, nursery)

    async def outcome(self) -> outcome.Outcome:
        async with self.result_chan:
            return await self.result_chan.receive()
