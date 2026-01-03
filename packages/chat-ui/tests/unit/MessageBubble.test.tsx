/**
 * Unit tests for MessageBubble component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '../../src/components/MessageBubble';
import type { Message } from '../../src/types';

// Mock the usePearlFlow hook
vi.mock('../../src/context/PearlFlowProvider', () => ({
  usePearlFlow: () => ({
    sendMessage: vi.fn(),
  }),
}));

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    const userMessage: Message = {
      id: '1',
      role: 'user',
      content: 'Hello, I have a toothache',
      timestamp: new Date('2024-01-01T10:00:00'),
    };

    render(<MessageBubble message={userMessage} />);

    const element = screen.getByText('Hello, I have a toothache');
    expect(element).toBeTruthy();
    expect(element.textContent).toBe('Hello, I have a toothache');
  });

  it('renders assistant message correctly', () => {
    const assistantMessage: Message = {
      id: '2',
      role: 'assistant',
      content: 'I understand, let me help you with that.',
      timestamp: new Date('2024-01-01T10:01:00'),
      agentName: 'Receptionist',
    };

    render(<MessageBubble message={assistantMessage} />);

    expect(screen.getByText('I understand, let me help you with that.')).toBeTruthy();
    expect(screen.getByText('Receptionist')).toBeTruthy();
  });

  it('renders assistant message with agent name', () => {
    const assistantMessage: Message = {
      id: '3',
      role: 'assistant',
      content: 'Can you tell me your pain level?',
      timestamp: new Date('2024-01-01T10:02:00'),
      agentName: 'IntakeSpecialist',
    };

    render(<MessageBubble message={assistantMessage} />);

    expect(screen.getByText('IntakeSpecialist')).toBeTruthy();
  });

  it('renders timestamp correctly', () => {
    const userMessage: Message = {
      id: '4',
      role: 'user',
      content: 'Test message',
      timestamp: new Date('2024-01-01T14:30:00'),
    };

    render(<MessageBubble message={userMessage} />);

    // Should show time in HH:MM format
    const element = screen.getByText(/14:30|2:30/);
    expect(element).toBeTruthy();
  });
});
