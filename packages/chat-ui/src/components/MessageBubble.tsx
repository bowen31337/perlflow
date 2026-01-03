import { clsx } from 'clsx';
import { useState } from 'react';
import type { Message, UIComponent } from '../types';
import { usePearlFlow } from '../context/PearlFlowProvider';
import { PainScaleSelector } from './PainScaleSelector';
import { DateTimePicker } from './DateTimePicker';
import { SlotList } from './SlotList';
import { ConfirmationCard } from './ConfirmationCard';
import { IncentiveOffer } from './IncentiveOffer';

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
 * Renders a generative UI component based on the type.
 */
function renderUIComponent(
  uiComponent: UIComponent,
  onInteraction: (response: string) => void
): JSX.Element | null {
  const { type, props } = uiComponent;

  switch (type) {
    case 'PainScaleSelector':
      return (
        <PainScaleSelector
          onSelect={(value) => onInteraction(`My pain level is ${value}`)}
          {...(props as any)}
        />
      );

    case 'DateTimePicker':
      return (
        <DateTimePicker
          onSelect={(date) => onInteraction(`I'd like to book for ${date.toLocaleString()}`)}
          {...(props as any)}
        />
      );

    case 'SlotList':
      return (
        <SlotList
          onSelect={(slot) => onInteraction(`I'll take the slot at ${slot.startTime.toLocaleString()}`)}
          {...(props as any)}
        />
      );

    case 'ConfirmationCard':
      return <ConfirmationCard {...(props as any)} />;

    case 'IncentiveOffer':
      return (
        <IncentiveOffer
          onAccept={() => onInteraction('I accept the offer')}
          onDecline={() => onInteraction('No thanks, I will keep my current appointment')}
          {...(props as any)}
        />
      );

    default:
      return (
        <div className="pf-text-xs pf-text-gray-500 pf-p-2 pf-bg-gray-50 pf-rounded">
          [UI Component: {type}]
        </div>
      );
  }
}

/**
 * Message bubble component that renders user and assistant messages.
 * Supports text, markdown, and generative UI components.
 */
export function MessageBubble({ message, className }: MessageBubbleProps): JSX.Element {
  const isUser = message.role === 'user';
  const { sendMessage } = usePearlFlow();
  const [uiInteracted, setUiInteracted] = useState(false);

  const handleUIInteraction = (response: string) => {
    setUiInteracted(true);
    sendMessage(response);
  };

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
        {message.content && (
          <div className="pf-text-sm pf-leading-relaxed pf-whitespace-pre-wrap pf-mb-2">
            {message.content}
          </div>
        )}

        {/* Render UI component if present */}
        {message.uiComponent && !uiInteracted && (
          <div className="pf-mt-2 pf-mb-2">
            {renderUIComponent(message.uiComponent, handleUIInteraction)}
          </div>
        )}

        {/* Show confirmation when UI was interacted with */}
        {uiInteracted && message.uiComponent && (
          <div className="pf-text-xs pf-text-gray-500 pf-italic pf-mt-1">
            ✓ Response sent
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
