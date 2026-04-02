import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiDataProvider, setUserId, clearUserId } from '@/data/api-provider';

function createSseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)));
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': 'text/event-stream' },
  });
}

describe('apiDataProvider assistant stream', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    clearUserId();
    sessionStorage.clear();
  });

  it('parses chunked SSE events for assistant streaming', async () => {
    setUserId('user-123');

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      createSseResponse([
        'id: 1\ndata: {"type":"response.delta","payload":{"index":1,"delta":"Hello"}}\n\n',
        'id: 2\ndata: {"type":"response.completed","payload":{"assistant_message_id":"msg-1","content":"Hello there"}}\n\n',
        'id: 3\ndata: {"type":"turn.completed","payload":{"status":"completed"}}\n\n',
      ]),
    );

    const received = {
      deltas: [] as string[],
      completed: null as null | { assistant_message_id?: string; content?: string },
      turnCompleted: 0,
      closed: 0,
    };

    await new Promise<void>((resolve, reject) => {
      apiDataProvider.streamAssistantTurn('stream-token', {
        onResponseDelta: (payload) => {
          if (payload.delta) received.deltas.push(payload.delta);
        },
        onResponseCompleted: (payload) => {
          received.completed = payload;
        },
        onTurnCompleted: () => {
          received.turnCompleted += 1;
        },
        onError: (error) => reject(new Error(error)),
        onClose: () => {
          received.closed += 1;
          resolve();
        },
      });
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:3000/api/assistant/streams/stream-token/events',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Accept: 'text/event-stream',
          'X-User-ID': 'user-123',
        }),
      }),
    );
    expect(received.deltas).toEqual(['Hello']);
    expect(received.completed).toEqual({
      assistant_message_id: 'msg-1',
      content: 'Hello there',
    });
    expect(received.turnCompleted).toBe(1);
    expect(received.closed).toBe(1);
  });
});
