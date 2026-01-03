import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Connection state for the SSE stream.
 */
export interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempts: number;
}

/**
 * SSE event received from the server.
 */
export interface SSEEvent {
  type: 'token' | 'agent_state' | 'ui_component' | 'complete' | 'error';
  data: unknown;
}

interface UseConnectionOptions {
  url: string;
  sessionId: string;
  onEvent?: (event: SSEEvent) => void;
  onError?: (error: Error) => void;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
}

/**
 * Hook for managing SSE connection with automatic reconnection.
 *
 * @example
 * ```tsx
 * const { isConnected, connect, disconnect } = useConnection({
 *   url: '/chat/stream',
 *   sessionId: 'abc-123',
 *   onEvent: (event) => console.log(event),
 * });
 * ```
 */
export function useConnection({
  url,
  sessionId,
  onEvent,
  onError,
  maxReconnectAttempts = 3,
  reconnectDelay = 1000,
}: UseConnectionOptions) {
  const [state, setState] = useState<ConnectionState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setState({
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0,
    });
  }, []);

  const connect = useCallback(() => {
    // Clean up any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setState((prev) => ({
      ...prev,
      isConnecting: true,
      error: null,
    }));

    const fullUrl = `${url}/${sessionId}`;
    const eventSource = new EventSource(fullUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setState({
        isConnected: true,
        isConnecting: false,
        error: null,
        reconnectAttempts: 0,
      });
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);

      eventSource.close();
      eventSourceRef.current = null;

      setState((prev) => {
        const newAttempts = prev.reconnectAttempts + 1;

        if (newAttempts <= maxReconnectAttempts) {
          // Schedule reconnection
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay * newAttempts);

          return {
            isConnected: false,
            isConnecting: false,
            error: `Connection lost. Reconnecting (attempt ${newAttempts}/${maxReconnectAttempts})...`,
            reconnectAttempts: newAttempts,
          };
        }

        const errorMessage = 'Connection failed after maximum retry attempts';
        onError?.(new Error(errorMessage));

        return {
          isConnected: false,
          isConnecting: false,
          error: errorMessage,
          reconnectAttempts: newAttempts,
        };
      });
    };

    // Handle different event types
    const handleEvent = (type: SSEEvent['type']) => (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        onEvent?.({ type, data });
      } catch (e) {
        // If not JSON, pass raw data
        onEvent?.({ type, data: event.data });
      }
    };

    eventSource.addEventListener('token', handleEvent('token'));
    eventSource.addEventListener('agent_state', handleEvent('agent_state'));
    eventSource.addEventListener('ui_component', handleEvent('ui_component'));
    eventSource.addEventListener('complete', handleEvent('complete'));
    eventSource.addEventListener('error', handleEvent('error'));
  }, [url, sessionId, onEvent, onError, maxReconnectAttempts, reconnectDelay]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    ...state,
    connect,
    disconnect,
  };
}
