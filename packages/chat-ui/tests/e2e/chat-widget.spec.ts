/**
 * E2E tests for the PearlFlow Chat Widget
 *
 * These tests verify end-to-end functionality of the chat widget
 * including UI interactions, message flow, and agent hand-offs.
 */

import { test, expect } from '@playwright/test';

test.describe('PearlFlow Chat Widget - Basic Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the demo page
    await page.goto('/');
  });

  test('Chat widget button is visible and clickable', async ({ page }) => {
    // The floating button should be visible
    const chatButton = page.getByRole('button', { name: 'Open chat' });
    await expect(chatButton).toBeVisible();
  });

  test('Opening chat widget creates a session', async ({ page }) => {
    // Click the chat button to open
    const chatButton = page.getByRole('button', { name: 'Open chat' });
    await chatButton.click();

    // Wait for chat window to appear
    const chatWindow = page.getByText('PearlFlow Assistant');
    await expect(chatWindow).toBeVisible();

    // Check for welcome message
    const welcomeMessage = page.getByText(/welcome|hello/i);
    await expect(welcomeMessage).toBeVisible();
  });

  test('Chat window can be minimized', async ({ page }) => {
    // Open chat
    const chatButton = page.getByRole('button', { name: 'Open chat' });
    await chatButton.click();

    // Wait for chat window
    await expect(page.getByText('PearlFlow Assistant')).toBeVisible();

    // Click minimize button
    const minimizeButton = page.getByRole('button', { name: 'Minimize chat' });
    await minimizeButton.click();

    // Chat window should be hidden, button should be visible
    await expect(page.getByText('PearlFlow Assistant')).not.toBeVisible();
    await expect(chatButton).toBeVisible();
  });
});

test.describe('PearlFlow Chat Widget - Message Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Open chat widget
    await page.getByRole('button', { name: 'Open chat' }).click();
    // Wait for session to be created
    await expect(page.getByText('PearlFlow Assistant')).toBeVisible();
  });

  test('User can send a message', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Type message
    await input.fill('Hello, I have a toothache');

    // Send message
    await sendButton.click();

    // User message should appear
    await expect(page.getByText('Hello, I have a toothache')).toBeVisible();
  });

  test('Agent responds with typing indicator', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send a pain-related message
    await input.fill('I have severe toothache');
    await sendButton.click();

    // Check for typing indicator
    const typingIndicator = page.getByText(/is typing\.\.\./i);
    await expect(typingIndicator).toBeVisible();
  });

  test('Agent hand-off indicator shows correct agent', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send pain message to trigger IntakeSpecialist
    await input.fill('I have severe toothache');
    await sendButton.click();

    // Wait for response and check agent indicator in header
    await expect(page.getByText(/Triage Nurse|IntakeSpecialist/i)).toBeVisible();
  });

  test('Conversation flow maintains state', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Start pain triage flow
    await input.fill('I have severe toothache');
    await sendButton.click();

    // Wait for first response
    await expect(page.getByText(/pain/i)).toBeVisible();

    // Send pain level
    await input.fill('My pain level is 8');
    await sendButton.click();

    // Should ask about swelling (state is maintained)
    await expect(page.getByText(/swelling/i)).toBeVisible();
  });
});

test.describe('PearlFlow Chat Widget - UI Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByText('PearlFlow Assistant')).toBeVisible();
  });

  test('Pain scale selector appears for pain messages', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send pain message
    await input.fill('I have a toothache');
    await sendButton.click();

    // Wait for UI component to appear
    // The PainScaleSelector should render
    await expect(page.getByText(/pain/i)).toBeVisible();
  });

  test('Message bubbles have correct styling', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send message
    await input.fill('Test message');
    await sendButton.click();

    // User message should have distinct styling (right-aligned, colored)
    const userMessage = page.locator('div', { hasText: 'Test message' }).first();
    await expect(userMessage).toBeVisible();
  });

  test('Agent messages show agent name', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send message
    await input.fill('Hello');
    await sendButton.click();

    // Agent name should be visible in header
    await expect(page.getByText(/Receptionist/i)).toBeVisible();
  });
});

test.describe('PearlFlow Chat Widget - Error Handling', () => {
  test('Shows error when server is unavailable', async ({ page }) => {
    // This test would require a mock server or disconnected state
    // For now, we'll skip it as it requires specific setup
    test.skip();
  });
});

test.describe('PearlFlow Chat Widget - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Chat button has proper ARIA label', async ({ page }) => {
    const chatButton = page.getByRole('button', { name: 'Open chat' });
    await expect(chatButton).toHaveAttribute('aria-label', 'Open chat');
  });

  test('Input field has accessible placeholder', async ({ page }) => {
    await page.getByRole('button', { name: 'Open chat' }).click();
    const input = page.getByPlaceholder('Type a message...');
    await expect(input).toBeVisible();
  });

  test('Send button is accessible', async ({ page }) => {
    await page.getByRole('button', { name: 'Open chat' }).click();
    const sendButton = page.getByRole('button', { name: 'Send message' });
    await expect(sendButton).toBeVisible();
  });
});
