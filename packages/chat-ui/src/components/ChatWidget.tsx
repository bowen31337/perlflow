import { useState, useEffect } from 'react';
import { usePearlFlow } from '../context/PearlFlowProvider';
import { ChatWindow } from './ChatWindow';
import { clsx } from 'clsx';

/**
 * Props for the ChatWidget component.
 */
export interface ChatWidgetProps {
  /** Position of the floating button */
  position?: 'bottom-right' | 'bottom-left';
  /** Whether the chat is open by default */
  defaultOpen?: boolean;
  /** Custom class name for the container */
  className?: string;
}

/**
 * Main embeddable chat widget component.
 * Renders a floating button that expands into a chat window.
 *
 * @example
 * ```tsx
 * <ChatWidget position="bottom-right" defaultOpen={false} />
 * ```
 */
export function ChatWidget({
  position = 'bottom-right',
  defaultOpen = false,
  className,
}: ChatWidgetProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const { createSession, session, theme } = usePearlFlow();

  // Create session when widget opens for the first time
  useEffect(() => {
    if (isOpen && !session) {
      createSession();
    }
  }, [isOpen, session, createSession]);

  const positionClasses = position === 'bottom-right'
    ? 'pf-right-4 pf-bottom-4'
    : 'pf-left-4 pf-bottom-4';

  return (
    <div
      className={clsx('pf-fixed pf-z-50', positionClasses, className)}
      style={{ '--pf-primary': theme.primary } as React.CSSProperties}
    >
      {isOpen ? (
        <div className="pf-animate-fade-in">
          <ChatWindow onClose={() => setIsOpen(false)} />
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className={clsx(
            'pf-w-14 pf-h-14 pf-rounded-full pf-shadow-lg',
            'pf-flex pf-items-center pf-justify-center',
            'pf-bg-primary pf-text-white',
            'pf-transition-transform pf-duration-200',
            'hover:pf-scale-110 focus:pf-outline-none focus:pf-ring-2 focus:pf-ring-primary focus:pf-ring-offset-2',
            'pf-animate-fade-in'
          )}
          aria-label="Open chat"
        >
          {/* Chat icon */}
          <svg
            className="pf-w-6 pf-h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
