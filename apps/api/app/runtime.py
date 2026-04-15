from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator


class EventHub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def publish(self, run_id: str, message: str) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(run_id, set()))

        for queue in subscribers:
            await queue.put(message)

    @asynccontextmanager
    async def subscribe(self, run_id: str) -> AsyncIterator[asyncio.Queue[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue()

        async with self._lock:
            self._subscribers[run_id].add(queue)

        try:
            yield queue
        finally:
            async with self._lock:
                subscribers = self._subscribers.get(run_id)
                if not subscribers:
                    return

                subscribers.discard(queue)
                if not subscribers:
                    self._subscribers.pop(run_id, None)
