/**
 * Shared types for the PearlFlow chat UI.
 */

/**
 * Represents a chat message in the conversation.
 */
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agentName?: string;
  uiComponent?: UIComponent;
}

/**
 * Represents the current state of the agent system.
 */
export interface AgentState {
  activeAgent: 'Receptionist' | 'IntakeSpecialist' | 'ResourceOptimiser';
  thinking: boolean;
  previousAgent?: string;
}

/**
 * Represents a generative UI component to render in the chat.
 */
export interface UIComponent {
  type:
    | 'PainScaleSelector'
    | 'DateTimePicker'
    | 'SlotList'
    | 'ConfirmationCard'
    | 'IncentiveOffer';
  props: Record<string, unknown>;
}

/**
 * Available appointment slot.
 */
export interface Slot {
  id: string;
  startTime: Date;
  endTime: Date;
  dentistId: string;
  dentistName: string;
  procedureCode?: string;
}

/**
 * Appointment confirmation details.
 */
export interface AppointmentConfirmation {
  appointmentId: string;
  patientName: string;
  procedureName: string;
  startTime: Date;
  dentistName: string;
}

/**
 * Incentive offer for rescheduling.
 */
export interface IncentiveOfferData {
  offerId: string;
  originalTime: Date;
  proposedTime: Date;
  incentiveType: 'discount' | 'priority_slot' | 'gift';
  incentiveValue: string;
  expiresAt: Date;
}

/**
 * Session information.
 */
export interface Session {
  sessionId: string;
  status: 'active' | 'completed' | 'abandoned';
  currentAgent: string;
}

/**
 * Theme configuration for the widget.
 */
export interface Theme {
  primary?: string;
  secondary?: string;
  accent?: string;
  background?: string;
  text?: string;
  fontFamily?: string;
}
