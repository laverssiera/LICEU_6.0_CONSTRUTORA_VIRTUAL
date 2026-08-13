import { useEffect } from 'react';
import { resolvedWsBaseUrl } from '@/services/runtimeConfig';

export default function useEventBus(onEvent) {
  useEffect(() => {
    const ws = new WebSocket(`${resolvedWsBaseUrl}/events/ws`);

    ws.onmessage = (msg) => {
      try {
        const envelope = JSON.parse(msg.data);
        const event = envelope?.event || envelope;
        onEvent(event);
      } catch (_error) {
        // Ignore malformed events to keep stream stable.
      }
    };

    return () => ws.close();
  }, [onEvent]);
}
