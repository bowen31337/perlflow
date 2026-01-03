import React from 'react';
import { clsx } from 'clsx';
import type { Message } from '../types';

/**
 * Props for the MessageBubble component.
 */
export interface MessageBubbleProps {
  /** The message to display */
  message: Message;
  /** Custom class name */
  className?: string;
}

/**
 * Message bubble component that renders user and assistant messages.
 * Supports text, markdown, and generative UI components.
 */
export function MessageBubble({ message, className }: MessageBubbleProps): JSX.Element {
  const isUser = message.role === 'user';

  return (
    <div
      className={clsx(
        'pf-flex pf-animate-slide-up',
        isUser ? 'pf-justify-end' : 'pf-justify-start',
        className
      )}
    >
      <div
        className={clsx(
          'pf-max-w-[80%] pf-rounded-2xl pf-px-4 pf-py-2',
          isUser
            ? 'pf-bg-primary pf-text-white pf-rounded-br-md'
            : 'pf-bg-gray-100 pf-text-gray-900 pf-rounded-bl-md'
        )}
      >
        {/* Agent name label for assistant messages */}
        {!isUser && message.agentName && (
          <div className="pf-text-xs pf-text-agent pf-font-medium pf-mb-1">
            {message.agentName}
          </div>
        )}

        {/* Message content */}
        <div className="pf-text-sm pf-leading-relaxed pf-whitespace-pre-wrap">
          {message.content}
        </div>

        {/* TODO: Render UI component if present */}
        {message.uiComponent && (
          <div className="pf-mt-2">
            {/* Placeholder for generative UI components */}
            <div className="pf-text-xs pf-text-gray-500">
              [UI Component: {message.uiComponent.type}]
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div
          className={clsx(
            'pf-text-xs pf-mt-1',
            isUser ? 'pf-text-white/70' : 'pf-text-gray-400'
          )}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}
