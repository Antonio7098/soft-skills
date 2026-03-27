"""In-memory generation realtime broker and execution registry."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from soft_skills_backend.modules.catalog.contracts.stream import GenerationStreamEvent

if TYPE_CHECKING:
    from stageflow.api import PipelineContext


@dataclass
class GenerationExecution:
    """Mutable execution handles for one live generation."""

    generation_id: str
    mode: str
    stream_token: str
    task: asyncio.Task[None] | None = None
    pipeline_context: PipelineContext | None = None
    cancel_reason: str | None = None
    is_cancelled: bool = False

    def request_cancel(self, reason: str) -> None:
        self.cancel_reason = reason
        self.is_cancelled = True
        if self.pipeline_context is not None:
            self.pipeline_context.mark_canceled()


@dataclass(frozen=True, slots=True)
class _Subscriber:
    queue: asyncio.Queue[GenerationStreamEvent]
    loop: asyncio.AbstractEventLoop


class GenerationRealtimeBroker:
    """Process-local publish/subscribe broker for generation stream events."""

    def __init__(self, *, backlog_size: int = 256) -> None:
        self._backlog_size = backlog_size
        self._backlog: dict[str, deque[GenerationStreamEvent]] = defaultdict(
            lambda: deque(maxlen=self._backlog_size)
        )
        self._subscribers: dict[str, dict[asyncio.Queue[GenerationStreamEvent], _Subscriber]] = (
            defaultdict(dict)
        )
        self._executions: dict[str, GenerationExecution] = {}

    def backlog(
        self, stream_token: str, *, after_sequence: int | None = None
    ) -> list[GenerationStreamEvent]:
        events = list(self._backlog[stream_token])
        if after_sequence is None:
            return events
        return [event for event in events if event.sequence_number > after_sequence]

    def subscribe(self, stream_token: str) -> asyncio.Queue[GenerationStreamEvent]:
        queue: asyncio.Queue[GenerationStreamEvent] = asyncio.Queue()
        self._subscribers[stream_token][queue] = _Subscriber(
            queue=queue,
            loop=asyncio.get_running_loop(),
        )
        return queue

    def unsubscribe(self, stream_token: str, queue: asyncio.Queue[GenerationStreamEvent]) -> None:
        subscribers = self._subscribers.get(stream_token)
        if subscribers is None:
            return
        subscribers.pop(queue, None)
        if not subscribers:
            self._subscribers.pop(stream_token, None)

    async def publish(self, stream_token: str, event: GenerationStreamEvent) -> None:
        self._backlog[stream_token].append(event)
        current_loop = asyncio.get_running_loop()
        for subscriber in list(self._subscribers.get(stream_token, {}).values()):
            if subscriber.loop is current_loop:
                await subscriber.queue.put(event)
                continue
            future = asyncio.run_coroutine_threadsafe(subscriber.queue.put(event), subscriber.loop)
            await asyncio.wrap_future(future)

    def register_execution(self, execution: GenerationExecution) -> None:
        self._executions[execution.generation_id] = execution

    def get_execution(self, generation_id: str) -> GenerationExecution | None:
        return self._executions.get(generation_id)

    def remove_execution(self, generation_id: str) -> None:
        self._executions.pop(generation_id, None)

    def get_execution_by_token(self, stream_token: str) -> GenerationExecution | None:
        for execution in self._executions.values():
            if execution.stream_token == stream_token:
                return execution
        return None
