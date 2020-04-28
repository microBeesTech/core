"""Helper to help coordinating calls."""
import asyncio
import functools
from typing import Awaitable, Callable, TypeVar, cast

from homeassistant.core import HomeAssistant

T = TypeVar("T")

FUNC = Callable[[HomeAssistant], Awaitable[T]]


def cache_per_instance(data_key: str) -> Callable[[FUNC], FUNC]:
    """Decorate a function that should be called once per instance.

    Result will be cached and simultaneous calls will be handled.
    """

    def wrapper(func: FUNC) -> FUNC:
        """Wrap a function with caching logic."""

        @functools.wraps(func)
        async def wrapped(hass: HomeAssistant) -> T:
            reg_or_evt = hass.data.get(data_key)

            if not reg_or_evt:
                evt = hass.data[data_key] = asyncio.Event()

                result = await func(hass)

                hass.data[data_key] = result
                evt.set()
                return cast(T, result)

            if isinstance(reg_or_evt, asyncio.Event):
                evt = reg_or_evt
                await evt.wait()
                return cast(T, hass.data.get(data_key))

            return cast(T, reg_or_evt)

        return wrapped

    return wrapper
