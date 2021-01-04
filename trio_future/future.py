from dataclasses import dataclass

import outcome
import trio


@dataclass
class Future:
    """Container class for the results of an async function.
    """

    # TODO we can type this!
    result_chan: trio.abc.ReceiveChannel
    nursery: trio.Nursery  # TODO not sure if we need this but feels like good practice

    async def get(self):
        """Await the result of this :class:`Future` and unwrap the value. This will return a plain object
        if successful. If the bound function raised an exception, this will re-raise it.

        :return: The result of the bound unfunction, unwrapped
        :rtype: The return type of the bound function.
        """
        future_outcome = await self.outcome()
        return future_outcome.unwrap()

    async def outcome(self) -> outcome.Outcome:
        """Await the result of this :class:`Future` and return it as an instance of ``outcome.Outcome``,
        which can be one of ``Value`` or ``Error``. Can only be called once for this object instance.

        :raises RuntimeError: If this method is called more than once on an object instance.
        :return: Outcome of the function captured by this :class:`Future`.
        :rtype: outcome.Outcome
        """
        try:
            async with self.result_chan:
                return await self.result_chan.receive()
        except trio.ClosedResourceError:
            raise RuntimeError(
                "Trio resource closed (did you try to call outcome twice on this future?"
            )
