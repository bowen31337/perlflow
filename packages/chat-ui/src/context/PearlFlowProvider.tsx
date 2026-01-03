import { createContext, useContext, useMemo, useState, useCallback, useRef, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { Session, AgentState, Message, UIComponent } from '../types';
import { useConnection, type SSEEvent } from '../hooks/useConnection';

/**
 * Theme configuration for customizing the widget appearance.
 */
export interface PearlFlowTheme {
  /** Primary brand color (default: #00D4FF) */
  primary?: string;
  /** Secondary color for success states (default: #10B981) */
  secondary?: string;
  /** Background color */
  background?: string;
  /** Text color */
  text?: string;
  /** Font family */
  fontFamily?: string;
}

/**
 * Props for the PearlFlowProvider component.
 */
export interface PearlFlowProviderProps {
  /** Clinic API key for authentication */
  apiKey: string;
  /** Optional API base URL (default: inferred from current origin) */
  apiUrl?: string;
  /** Theme customization */
  theme?: PearlFlowTheme;
  /** Child components */
  children: ReactNode;
}

interface PearlFlowContextValue {
  apiKey: string;
  apiUrl: string;
  theme: PearlFlowTheme;
  session: Session | null;
  agentState: AgentState;
  messages: Message[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  createSession: () => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  clearError: () => void;
}

const defaultTheme: PearlFlowTheme = {
  primary: '#00D4FF',
  secondary: '#10B981',
  background: '#FFFFFF',
  text: '#111827',
  fontFamily: 'Inter, system-ui, sans-serif',
};

const PearlFlowContext = createContext<PearlFlowContextValue | null>(null);

/**
 * Provider component that wraps your app to enable PearlFlow chat functionality.
 *
 * @example
 * ```tsx
 * <PearlFlowProvider apiKey="pf_live_..." theme={{ primary: '#00D4FF' }}>
 *   <ChatWidget position="bottom-right" />
 * </PearlFlowProvider>
 * ```
 */
export function PearlFlowProvider({
  apiKey,
  apiUrl = '',
  theme: customTheme,
  children,
}: PearlFlowProviderProps): JSX.Element {
  const [session, setSession] = useState<Session | null>(null);
  const [agentState, setAgentState] = useState<AgentState>({
    activeAgent: 'Receptionist',
    thinking: false,
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track current assistant message being built from SSE tokens
  const currentAssistantMessageRef = useRef<{
    id: string;
    content: string;
    agentName: string;
    uiComponent?: UIComponent;
  } | null>(null);

  const theme = useMemo(() => ({ ...defaultTheme, ...customTheme }), [customTheme]);

  // SSE event handler
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'agent_state':
        if (typeof event.data === 'object' && event.data !== null) {
          const data = event.data as { active_agent?: string; thinking?: boolean };
          if (data.active_agent) {
            const activeAgent = data.active_agent as AgentState['activeAgent'];
            setAgentState((prev) => ({
              activeAgent: activeAgent || prev.activeAgent,
              thinking: data.thinking ?? prev.thinking,
            }));
          }
        }
        break;

      case 'ui_component':
        // Store UI component for the current or next assistant message
        if (typeof event.data === 'object' && event.data !== null) {
          const data = event.data as { type: string; props: Record<string, unknown> };
          // If there's a current message being built, attach to it
          if (currentAssistantMessageRef.current) {
            currentAssistantMessageRef.current.uiComponent = {
              type: data.type as UIComponent['type'],
              props: data.props,
            };
          } else {
            // Create a pending message with UI component to be attached to the next message
            // This handles the case where ui_component comes before token events
            currentAssistantMessageRef.current = {
              id: crypto.randomUUID(),
              content: '',
              agentName: agentState.activeAgent,
              uiComponent: {
                type: data.type as UIComponent['type'],
                props: data.props,
              },
            };
          }
        }
        break;

      case 'token':
        // Start a new assistant message or append to existing
        if (!currentAssistantMessageRef.current) {
          currentAssistantMessageRef.current = {
            id: crypto.randomUUID(),
            content: '',
            agentName: agentState.activeAgent,
          };
        }

        if (typeof event.data === 'object' && event.data !== null) {
          const data = event.data as { text?: string };
          if (data.text && currentAssistantMessageRef.current) {
            currentAssistantMessageRef.current.content += data.text;

            // Update messages with partial content
            setMessages((prev) => {
              // Find if we already have this message in progress
              const existingIndex = prev.findIndex(
                (m) => m.id === currentAssistantMessageRef.current?.id
              );

              if (existingIndex >= 0) {
                // Update existing message
                const updated = [...prev];
                updated[existingIndex] = {
                  ...updated[existingIndex],
                  content: currentAssistantMessageRef.current!.content,
                  uiComponent: currentAssistantMessageRef.current!.uiComponent,
                };
                return updated;
              } else {
                // Add new message
                return [
                  ...prev,
                  {
                    id: currentAssistantMessageRef.current!.id,
                    role: 'assistant',
                    content: currentAssistantMessageRef.current!.content,
                    timestamp: new Date(),
                    agentName: currentAssistantMessageRef.current!.agentName,
                    uiComponent: currentAssistantMessageRef.current!.uiComponent,
                  },
                ];
              }
            });
          }
        }
        break;

      case 'complete':
        // Reset tracking
        currentAssistantMessageRef.current = null;
        setIsLoading(false);
        setAgentState((prev) => ({ ...prev, thinking: false }));
        break;

      case 'error':
        setError(typeof event.data === 'string' ? event.data : 'Stream error');
        setIsLoading(false);
        setAgentState((prev) => ({ ...prev, thinking: false }));
        break;
    }
  }, [agentState.activeAgent]);

  // Connection hook for SSE
  const {
    isConnected: sseConnected,
    isConnecting,
    connect: sseConnect,
    disconnect: sseDisconnect,
  } = useConnection({
    url: `${apiUrl}/chat/stream`,
    sessionId: session?.sessionId || '',
    onEvent: handleSSEEvent,
    onError: (err) => {
      setError(err.message);
      setIsLoading(false);
      setAgentState((prev) => ({ ...prev, thinking: false }));
    },
    maxReconnectAttempts: 3,
    reconnectDelay: 1000,
  });

  // Sync SSE connection state
  useEffect(() => {
    setIsConnected(sseConnected);
  }, [sseConnected]);

  // Auto-connect when session is created
  useEffect(() => {
    if (session && !sseConnected && !isConnecting) {
      sseConnect();
    }
  }, [session, sseConnected, isConnecting, sseConnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      sseDisconnect();
    };
  }, [sseDisconnect]);

  const createSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ clinic_api_key: apiKey }),
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      const data = await response.json();
      setSession({
        sessionId: data.session_id,
        status: 'active',
        currentAgent: 'Receptionist',
      });

      // Add welcome message
      if (data.welcome_message) {
        setMessages([
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: data.welcome_message,
            timestamp: new Date(),
            agentName: 'Receptionist',
          },
        ]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [apiKey, apiUrl]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!session) {
        setError('No active session');
        return;
      }

      if (!sseConnected) {
        setError('Not connected to server');
        return;
      }

      // Add user message immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      setIsLoading(true);
      setAgentState((prev) => ({ ...prev, thinking: true }));

      try {
        // Send message to API
        const response = await fetch(`${apiUrl}/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: session.sessionId,
            text,
          }),
        });

        if (!response.ok) {
          throw new Error(`Server returned ${response.status}`);
        }

        // The SSE stream will handle the response automatically
        // via the onEvent callback
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
        setIsLoading(false);
        setAgentState((prev) => ({ ...prev, thinking: false }));
      }
    },
    [session, apiUrl, sseConnected]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value = useMemo(
    () => ({
      apiKey,
      apiUrl,
      theme,
      session,
      agentState,
      messages,
      isConnected,
      isLoading,
      error,
      createSession,
      sendMessage,
      clearError,
    }),
    [
      apiKey,
      apiUrl,
      theme,
      session,
      agentState,
      messages,
      isConnected,
      isLoading,
      error,
      createSession,
      sendMessage,
      clearError,
    ]
  );

  return (
    <PearlFlowContext.Provider value={value}>
      {children}
    </PearlFlowContext.Provider>
  );
}

/**
 * Hook to access the PearlFlow context.
 * Must be used within a PearlFlowProvider.
 */
export function usePearlFlow(): PearlFlowContextValue {
  const context = useContext(PearlFlowContext);
  if (!context) {
    throw new Error('usePearlFlow must be used within a PearlFlowProvider');
  }
  return context;
}
