import { clsx } from 'clsx';

/**
 * Props for the AgentIndicator component.
 */
export interface AgentIndicatorProps {
  /** Name of the active agent */
  agentName: string;
  /** Whether the agent is currently thinking/processing */
  thinking?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Visual indicator showing which agent is currently active.
 * Displays the agent name and thinking status.
 */
export function AgentIndicator({
  agentName,
  thinking = false,
  className,
}: AgentIndicatorProps): JSX.Element {
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

  return (
    <div className={clsx('pf-flex pf-items-center pf-gap-1 pf-text-xs', className)}>
      <span>{icon}</span>
      <span className="pf-font-medium">{displayName}</span>
      {thinking && (
        <span className="pf-italic pf-opacity-80"> is thinking...</span>
      )}
    </div>
  );
}
