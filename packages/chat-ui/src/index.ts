/**
 * @pearlflow/chat-ui
 *
 * Embeddable React chat widget for PearlFlow dental AI assistant.
 *
 * @example
 * ```tsx
 * import { PearlFlowProvider, ChatWidget } from '@pearlflow/chat-ui';
 * import '@pearlflow/chat-ui/style.css';
 *
 * function App() {
 *   return (
 *     <PearlFlowProvider apiKey="pf_live_...">
 *       <ChatWidget position="bottom-right" defaultOpen={false} />
 *     </PearlFlowProvider>
 *   );
 * }
 * ```
 */

// Context Provider
export { PearlFlowProvider } from './context/PearlFlowProvider';
export type { PearlFlowProviderProps, PearlFlowTheme } from './context/PearlFlowProvider';

// Main Components
export { ChatWidget } from './components/ChatWidget';
export type { ChatWidgetProps } from './components/ChatWidget';

export { ChatWindow } from './components/ChatWindow';
export type { ChatWindowProps } from './components/ChatWindow';

export { MessageBubble } from './components/MessageBubble';
export type { MessageBubbleProps } from './components/MessageBubble';

export { AgentIndicator } from './components/AgentIndicator';
export type { AgentIndicatorProps } from './components/AgentIndicator';

// Generative UI Components
export { PainScaleSelector } from './components/PainScaleSelector';
export { DateTimePicker } from './components/DateTimePicker';
export { SlotList } from './components/SlotList';
export { ConfirmationCard } from './components/ConfirmationCard';
export { IncentiveOffer } from './components/IncentiveOffer';

// Hooks
export { useConnection } from './hooks/useConnection';
export type { ConnectionState, SSEEvent } from './hooks/useConnection';

// Types
export type { Message, AgentState, UIComponent } from './types';

// Styles
import './styles/index.css';
