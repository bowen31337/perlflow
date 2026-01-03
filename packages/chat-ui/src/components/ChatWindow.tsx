import React, { useRef, useEffect, useState } from 'react';
import { usePearlFlow } from '../context/PearlFlowProvider';
import { MessageBubble } from './MessageBubble';
import { AgentIndicator } from './AgentIndicator';
import { clsx } from 'clsx';

/**
 * Props for the ChatWindow component.
 */
export interface ChatWindowProps {
  /** Callback when close button is clicked */
  onClose?: () => void;
  /** Custom class name */
  className?: string;
}

/**
 * Main chat window container with header, messages, and input.
 */
export function ChatWindow({ onClose, className }: ChatWindowProps): JSX.Element {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { messages, agentState, isLoading, sendMessage, theme } = usePearlFlow();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    sendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div
      className={clsx(
        'pf-w-96 pf-h-[600px] pf-max-h-[80vh]',
        'pf-bg-white pf-rounded-2xl pf-shadow-2xl',
        'pf-flex pf-flex-col pf-overflow-hidden',
        'pf-border pf-border-gray-200',
        className
      )}
    >
      {/* Header */}
      <div
        className="pf-flex pf-items-center pf-justify-between pf-px-4 pf-py-3 pf-border-b pf-border-gray-200"
        style={{ backgroundColor: theme.primary }}
      >
        <div className="pf-flex pf-items-center pf-gap-3">
          {/* Logo/Avatar */}
          <div className="pf-w-10 pf-h-10 pf-rounded-full pf-bg-white/20 pf-flex pf-items-center pf-justify-center">
            <span className="pf-text-white pf-text-lg">🦷</span>
          </div>
          <div>
            <h3 className="pf-text-white pf-font-semibold pf-text-sm">PearlFlow Assistant</h3>
            <AgentIndicator
              agentName={agentState.activeAgent}
              thinking={agentState.thinking}
              className="pf-text-white/80"
            />
          </div>
        </div>

        <div className="pf-flex pf-gap-1">
          {/* Minimize button */}
          <button
            onClick={onClose}
            className="pf-p-2 pf-text-white/80 hover:pf-text-white pf-rounded-lg hover:pf-bg-white/10 pf-transition-colors"
            aria-label="Minimize chat"
          >
            <svg className="pf-w-5 pf-h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Close button */}
          <button
            onClick={onClose}
            className="pf-p-2 pf-text-white/80 hover:pf-text-white pf-rounded-lg hover:pf-bg-white/10 pf-transition-colors"
            aria-label="Close chat"
          >
            <svg className="pf-w-5 pf-h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages area */}
      <div className="pf-flex-1 pf-overflow-y-auto pf-p-4 pf-space-y-4">
        {messages.length === 0 ? (
          <div className="pf-text-center pf-text-gray-500 pf-py-8">
            <p className="pf-text-sm">Welcome! How can I help you today?</p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}

        {/* Typing indicator */}
        {agentState.thinking && (
          <div className="pf-flex pf-items-center pf-gap-2 pf-text-gray-500 pf-text-sm">
            <div className="pf-flex pf-gap-1">
              <span className="pf-w-2 pf-h-2 pf-rounded-full pf-bg-gray-400 pf-animate-typing-dot" style={{ animationDelay: '0ms' }} />
              <span className="pf-w-2 pf-h-2 pf-rounded-full pf-bg-gray-400 pf-animate-typing-dot" style={{ animationDelay: '200ms' }} />
              <span className="pf-w-2 pf-h-2 pf-rounded-full pf-bg-gray-400 pf-animate-typing-dot" style={{ animationDelay: '400ms' }} />
            </div>
            <span>{agentState.activeAgent} is typing...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="pf-p-4 pf-border-t pf-border-gray-200">
        <div className="pf-flex pf-gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isLoading}
            className={clsx(
              'pf-flex-1 pf-px-4 pf-py-2 pf-rounded-full',
              'pf-border pf-border-gray-300 pf-bg-gray-50',
              'focus:pf-outline-none focus:pf-ring-2 focus:pf-ring-primary focus:pf-border-transparent',
              'pf-text-sm pf-placeholder-gray-400',
              'disabled:pf-opacity-50 disabled:pf-cursor-not-allowed'
            )}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className={clsx(
              'pf-w-10 pf-h-10 pf-rounded-full',
              'pf-flex pf-items-center pf-justify-center',
              'pf-bg-primary pf-text-white',
              'pf-transition-all pf-duration-200',
              'hover:pf-bg-primary/90 focus:pf-outline-none focus:pf-ring-2 focus:pf-ring-primary focus:pf-ring-offset-2',
              'disabled:pf-opacity-50 disabled:pf-cursor-not-allowed'
            )}
            aria-label="Send message"
          >
            <svg className="pf-w-5 pf-h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
