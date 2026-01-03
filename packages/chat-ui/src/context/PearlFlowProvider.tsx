import React, { createContext, useContext, useMemo, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { Session, AgentState, Message } from '../types';

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

const defaultAgentState: AgentState = {
  activeAgent: 'Receptionist',
  thinking: false,
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
  const [agentState, setAgentState] = useState<AgentState>(defaultAgentState);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const theme = useMemo(() => ({ ...defaultTheme, ...customTheme }), [customTheme]);

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

      setIsConnected(true);
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
        await fetch(`${apiUrl}/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: session.sessionId,
            text,
          }),
        });

        // TODO: Connect to SSE stream for response
        // For now, add placeholder response
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: "I'm processing your request...",
          timestamp: new Date(),
          agentName: agentState.activeAgent,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
      } finally {
        setIsLoading(false);
        setAgentState((prev) => ({ ...prev, thinking: false }));
      }
    },
    [session, apiUrl, agentState.activeAgent]
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
