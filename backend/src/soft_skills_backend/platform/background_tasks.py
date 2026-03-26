"""Application-scoped background task scheduling."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any


class BackgroundTaskRunner:
    """Schedule coroutines onto the application lifespan loop."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._tasks: set[asyncio.Task[Any]] = set()
        self._errors: list[BaseException] = []

    def attach(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def start(self, coro: Coroutine[Any, Any, Any]) -> None:
        loop = self._loop
        if loop is None:
            asyncio.get_running_loop().create_task(coro)
            return

        def _spawn() -> None:
            task = loop.create_task(coro)
            self._tasks.add(task)
            task.add_done_callback(self._handle_task_done)

        if loop.is_running():
            loop.call_soon_threadsafe(_spawn)
            return
        asyncio.get_running_loop().create_task(coro)

    async def shutdown(self) -> None:
        if not self._tasks:
            return
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()

    def pop_errors(self) -> list[BaseException]:
        errors = list(self._errors)
        self._errors.clear()
        return errors

    def _handle_task_done(self, task: asyncio.Task[Any]) -> None:
        self._tasks.discard(task)
        try:
            exception = task.exception()
        except asyncio.CancelledError:
            return
        if exception is not None:
            self._errors.append(exception)
