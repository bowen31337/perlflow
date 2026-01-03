import { clsx } from 'clsx';
import { useEffect, useState } from 'react';

/**
 * Props for the AgentIndicator component.
 */
export interface AgentIndicatorProps {
  /** Name of the active agent */
  agentName: string;
  /** Whether the agent is currently thinking/processing */
  thinking?: boolean;
  /** Name of the previous agent (for hand-off animation) */
  previousAgent?: string;
  /** Custom class name */
  className?: string;
}

/**
 * Visual indicator showing which agent is currently active.
 * Displays the agent name, thinking status, and hand-off animations.
 */
export function AgentIndicator({
  agentName,
  thinking = false,
  previousAgent,
  className,
}: AgentIndicatorProps): JSX.Element {
  const [isHandOff, setIsHandOff] = useState(false);
  const [showPrevious, setShowPrevious] = useState(false);

  // Get display name and icon for each agent
  const getAgentDisplay = (name: string) => {
    switch (name) {
      case 'IntakeSpecialist':
        return { displayName: 'Triage Nurse', icon: '🩺' };
      case 'ResourceOptimiser':
        return { displayName: 'Scheduler', icon: '📅' };
      case 'Receptionist':
      default:
        return { displayName: 'Receptionist', icon: '👋' };
    }
  };

  const { displayName, icon } = getAgentDisplay(agentName);
  const previousDisplay = previousAgent ? getAgentDisplay(previousAgent) : null;

  // Trigger hand-off animation when agent changes
  useEffect(() => {
    if (previousAgent && previousAgent !== agentName) {
      setIsHandOff(true);
      setShowPrevious(true);

      // Hide previous agent after animation completes
      const timer = setTimeout(() => {
        setShowPrevious(false);
      }, 500);

      // Reset hand-off state after animation
      const resetTimer = setTimeout(() => {
        setIsHandOff(false);
      }, 1500);

      return () => {
        clearTimeout(timer);
        clearTimeout(resetTimer);
      };
    }
  }, [agentName, previousAgent]);

  return (
    <div className={clsx('pf-flex pf-items-center pf-gap-1 pf-text-xs', className)}>
      {/* Show previous agent during hand-off */}
      {showPrevious && previousDisplay && (
        <span className={clsx(
          'pf-opacity-60 pf-transition-all pf-duration-500',
          'pf-text-xs pf-mr-1'
        )}>
          {previousDisplay.icon} {previousDisplay.displayName}
          <span className="pf-ml-1 pf-text-gray-400">→</span>
        </span>
      )}

      {/* Current agent with hand-off animation */}
      <span
        className={clsx(
          isHandOff && 'pf-animate-agent-switch',
          isHandOff && 'pf-font-bold'
        )}
        title={isHandOff ? `Hand-off: ${previousDisplay?.displayName} → ${displayName}` : undefined}
      >
        {icon}
      </span>
      <span
        className={clsx(
          'pf-font-medium',
          isHandOff && 'pf-animate-agent-switch'
        )}
      >
        {displayName}
      </span>

      {/* Thinking indicator */}
      {thinking && (
        <span className="pf-italic pf-opacity-80"> is thinking...</span>
      )}

      {/* Hand-off badge (shows briefly during transition) */}
      {isHandOff && (
        <span className="pf-ml-1 pf-text-[10px] pf-px-1.5 pf-py-0.5 pf-bg-agent/20 pf-text-agent pf-rounded pf-animate-hand-off-pulse">
          Hand-off
        </span>
      )}
    </div>
  );
}
