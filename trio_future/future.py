from dataclasses import dataclass

import outcome
import trio


@dataclass
class Future:

    # TODO we can type this!
    result_chan: trio.abc.ReceiveChannel
    nursery: trio.Nursery  # TODO not sure if we need this but feels like good practice

    async def get(self):
        future_outcome = await self.outcome()
        return future_outcome.unwrap()

    async def outcome(self) -> outcome.Outcome:
        try:
            async with self.result_chan:
                return await self.result_chan.receive()
        except trio.ClosedResourceError:
            raise RuntimeError(
                "Trio resource closed (did you try to call outcome twice on this future?"
            )
