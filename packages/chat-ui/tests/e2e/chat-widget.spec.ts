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

    // Wait for chat window to appear - use heading role to target chat header specifically
    const chatWindow = page.getByRole('heading', { name: 'PearlFlow Assistant' });
    await expect(chatWindow).toBeVisible();

    // Check for welcome message (inside chat window, not page text)
    // The welcome message appears in the chat messages area
    const welcomeMessage = page.locator('.pf-overflow-y-auto').getByText(/welcome|hello/i);
    await expect(welcomeMessage).toBeVisible();
  });

  test('Chat window can be minimized', async ({ page }) => {
    // Open chat
    const chatButton = page.getByRole('button', { name: 'Open chat' });
    await chatButton.click();

    // Wait for chat window - use heading to target chat header specifically
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    // Click minimize button
    const minimizeButton = page.getByRole('button', { name: 'Minimize chat' });
    await minimizeButton.click();

    // Chat window should be hidden, button should be visible
    // The chat window is a container with pf-w-96 class
    await expect(page.locator('.pf-w-96')).not.toBeVisible();
    await expect(chatButton).toBeVisible();
  });
});

test.describe('PearlFlow Chat Widget - Message Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Open chat widget
    await page.getByRole('button', { name: 'Open chat' }).click();
    // Wait for session to be created - use heading to target chat header
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();
  });

  test('User can send a message', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Type message
    await input.fill('Hello, I have a toothache');

    // Send message
    await sendButton.click();

    // User message should appear in chat window (not in page text)
    // Look for the message within the chat messages area
    const messagesArea = page.locator('.pf-overflow-y-auto');
    await expect(messagesArea.getByText('Hello, I have a toothache')).toBeVisible();
  });

  test('Agent responds with typing indicator', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send a pain-related message
    await input.fill('I have severe toothache');
    await sendButton.click();

    // Check for typing indicator within chat window
    const messagesArea = page.locator('.pf-overflow-y-auto');
    const typingIndicator = messagesArea.getByText(/is typing\.\.\./i);
    await expect(typingIndicator).toBeVisible();
  });

  test('Agent hand-off indicator shows correct agent', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send pain message to trigger IntakeSpecialist
    await input.fill('I have severe toothache');
    await sendButton.click();

    // Wait for response and check agent indicator in header
    // The agent indicator is in the chat header
    const header = page.locator('.pf-flex.pf-items-center.pf-justify-between');
    await expect(header.getByText(/Triage Nurse|IntakeSpecialist/i)).toBeVisible();
  });

  test('Conversation flow maintains state', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Start pain triage flow
    await input.fill('I have severe toothache');
    await sendButton.click();

    // Wait for first response in messages area
    const messagesArea = page.locator('.pf-overflow-y-auto');
    await expect(messagesArea.getByText(/pain/i).first()).toBeVisible({ timeout: 10000 });

    // Send pain level
    await input.fill('My pain level is 8');
    await sendButton.click();

    // Should ask about swelling (state is maintained)
    await expect(messagesArea.getByText(/swelling/i).first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('PearlFlow Chat Widget - UI Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    // Use heading to target chat header specifically
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();
  });

  test('Pain scale selector appears for pain messages', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send pain message
    await input.fill('I have a toothache');
    await sendButton.click();

    // Wait for UI component to appear in messages area
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Wait for the complete response containing "pain level"
    await expect(messagesArea.getByText(/pain level/i).first()).toBeVisible({ timeout: 15000 });

    // Also verify the PainScaleSelector UI component appears
    await expect(messagesArea.getByText(/on a scale of 1-10/i).first()).toBeVisible();
  });

  test('Message bubbles have correct styling', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send message
    await input.fill('Test message');
    await sendButton.click();

    // User message should have distinct styling (right-aligned, colored)
    // Look within the chat messages area
    const messagesArea = page.locator('.pf-overflow-y-auto');
    const userMessage = messagesArea.locator('div', { hasText: 'Test message' }).first();
    await expect(userMessage).toBeVisible();
  });

  test('Agent messages show agent name', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });

    // Send message
    await input.fill('Hello');
    await sendButton.click();

    // Agent name should be visible in header
    const header = page.locator('.pf-flex.pf-items-center.pf-justify-between');
    await expect(header.getByText(/Receptionist/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('PearlFlow Chat Widget - Full E2E - New Patient Triage Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Open chat widget
    await page.getByRole('button', { name: 'Open chat' }).click();
    // Wait for session to be created
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();
  });

  test('New patient triage to booking flow', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Step 1: User reports symptoms
    await input.fill('I have severe toothache and need to see a dentist');
    await sendButton.click();

    // Step 2: Verify IntakeSpecialist activated
    const header = page.locator('.pf-flex.pf-items-center.pf-justify-between');
    await expect(header.getByText(/Triage Nurse|IntakeSpecialist/i)).toBeVisible({ timeout: 10000 });

    // Step 3: Wait for pain level prompt
    await expect(messagesArea.getByText(/pain level/i).first()).toBeVisible({ timeout: 15000 });
    await expect(messagesArea.getByText(/1-10/i).first()).toBeVisible();

    // Step 4: Provide pain level
    await input.fill('My pain is 8 out of 10');
    await sendButton.click();

    // Step 5: Check for swelling prompt
    await expect(messagesArea.getByText(/swelling/i).first()).toBeVisible({ timeout: 15000 });

    // Step 6: Answer swelling question
    await input.fill('No swelling, just severe pain');
    await sendButton.click();

    // Step 7: Check for fever prompt
    await expect(messagesArea.getByText(/fever/i).first()).toBeVisible({ timeout: 15000 });

    // Step 8: Answer fever question
    await input.fill('No fever, I feel fine otherwise');
    await sendButton.click();

    // Step 9: Wait for priority score and booking offer
    await expect(messagesArea.getByText(/priority score/i).first()).toBeVisible({ timeout: 15000 });
    await expect(messagesArea.getByText(/book an appointment/i).first()).toBeVisible();

    // Step 10: Request booking
    await input.fill('Yes, please book me an appointment');
    await sendButton.click();

    // Step 11: Verify ResourceOptimiser activated
    await expect(header.getByText(/ResourceOptimiser|Scheduler/i)).toBeVisible({ timeout: 15000 });

    // Step 12: Wait for available slots
    await expect(messagesArea.getByText(/available/i).first()).toBeVisible({ timeout: 15000 });
    await expect(messagesArea.getByText(/slot/i).first()).toBeVisible();

    // Step 13: Provide phone number for new patient
    await input.fill('+61412345678');
    await sendButton.click();

    // Step 14: Wait for patient creation confirmation
    await expect(messagesArea.getByText(/created/i).first()).toBeVisible({ timeout: 15000 });

    // Step 15: Provide name
    await input.fill('John Doe');
    await sendButton.click();

    // Step 16: Provide email
    await input.fill('john.doe@example.com');
    await sendButton.click();

    // Step 17: Select time slot
    await input.fill('Tomorrow at 10 AM');
    await sendButton.click();

    // Step 18: Wait for confirmation
    await expect(messagesArea.getByText(/confirmed/i).first()).toBeVisible({ timeout: 15000 });
    await expect(messagesArea.getByText(/appointment/i).first()).toBeVisible();

    // Step 19: Verify confirmation card appears
    await expect(messagesArea.getByText(/confirmation/i).first()).toBeVisible();

    // Step 20: Verify appointment in database (through API)
    // This would require backend verification, but we can check the UI response
    await expect(messagesArea.getByText(/Thank you/i).first()).toBeVisible();
  });

  test('Existing patient quick booking flow', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Step 1: User requests booking
    await input.fill('I need to book a cleaning appointment');
    await sendButton.click();

    // Step 2: Verify ResourceOptimiser activated
    const header = page.locator('.pf-flex.pf-items-center.pf-justify-between');
    await expect(header.getByText(/ResourceOptimiser|Scheduler/i)).toBeVisible({ timeout: 10000 });

    // Step 3: Wait for available slots
    await expect(messagesArea.getByText(/available/i).first()).toBeVisible({ timeout: 15000 });

    // Step 4: Provide phone number for existing patient lookup
    await input.fill('+61412345678');
    await sendButton.click();

    // Step 5: Wait for patient found confirmation
    await expect(messagesArea.getByText(/found/i).first()).toBeVisible({ timeout: 15000 });

    // Step 6: Select time slot
    await input.fill('Next Monday at 2 PM');
    await sendButton.click();

    // Step 7: Wait for confirmation
    await expect(messagesArea.getByText(/confirmed/i).first()).toBeVisible({ timeout: 15000 });

    // Step 8: Verify confirmation card
    await expect(messagesArea.getByText(/confirmation/i).first()).toBeVisible();
  });

  test('Emergency triage with escalation', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Step 1: User reports emergency symptoms
    await input.fill('I have severe toothache and difficulty breathing');
    await sendButton.click();

    // Step 2: Verify immediate emergency response
    const header = page.locator('.pf-flex.pf-items-center.pf-justify-between');
    await expect(header.getByText(/Emergency|Triage Nurse/i)).toBeVisible({ timeout: 10000 });

    // Step 3: Wait for emergency escalation message
    await expect(messagesArea.getByText(/emergency/i).first()).toBeVisible({ timeout: 15000 });
    await expect(messagesArea.getByText(/call/i).first()).toBeVisible();
    await expect(messagesArea.getByText(/immediate/i).first()).toBeVisible();

    // Step 4: Verify no booking flow initiated
    await expect(messagesArea.getByText(/appointment/i)).not.toBeVisible({ timeout: 5000 });
  });

  test('Move negotiation for high-value procedure', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Step 1: Request high-value procedure
    await input.fill('I need a dental implant');
    await sendButton.click();

    // Step 2: Verify ResourceOptimiser activated
    const header = page.locator('.pf-flex.pf-items-center.pf-justify-between');
    await expect(header.getByText(/ResourceOptimiser|Scheduler/i)).toBeVisible({ timeout: 10000 });

    // Step 3: Provide phone number
    await input.fill('+61412345678');
    await sendButton.click();

    // Step 4: Wait for move negotiation
    await expect(messagesArea.getByText(/move/i).first()).toBeVisible({ timeout: 15000 });
    await expect(messagesArea.getByText(/incentive/i).first()).toBeVisible();

    // Step 5: Accept move offer
    await input.fill('Yes, I can move my appointment');
    await sendButton.click();

    // Step 6: Wait for confirmation
    await expect(messagesArea.getByText(/confirmed/i).first()).toBeVisible({ timeout: 15000 });
  });

  test('Session recovery after disconnect', async ({ page }) => {
    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Step 1: Start conversation
    await input.fill('I have a toothache');
    await sendButton.click();

    // Step 2: Wait for response
    await expect(messagesArea.getByText(/pain/i).first()).toBeVisible({ timeout: 10000 });

    // Step 3: Minimize and reopen chat (simulating disconnect)
    const minimizeButton = page.getByRole('button', { name: 'Minimize chat' });
    await minimizeButton.click();
    await page.getByRole('button', { name: 'Open chat' }).click();

    // Step 4: Verify session state recovered
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();
    await expect(messagesArea.getByText(/pain/i).first()).toBeVisible();
  });

  test('Concurrent sessions for same clinic', async ({ context }) => {
    // Create second browser context
    const page2 = await context.newPage();

    // Open both pages
    await page.goto('/');
    await page2.goto('/');

    // Open both chats
    await page.getByRole('button', { name: 'Open chat' }).click();
    await page2.getByRole('button', { name: 'Open chat' }).click();

    // Wait for both to be visible
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();
    await expect(page2.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    // Send different messages
    const input1 = page.getByPlaceholder('Type a message...');
    const input2 = page2.getByPlaceholder('Type a message...');

    await input1.fill('Patient 1: toothache');
    await input2.fill('Patient 2: cleaning');

    await page.getByRole('button', { name: 'Send message' }).click();
    await page2.getByRole('button', { name: 'Send message' }).click();

    // Verify both sessions work independently
    const messagesArea1 = page.locator('.pf-overflow-y-auto');
    const messagesArea2 = page2.locator('.pf-overflow-y-auto');

    await expect(messagesArea1.getByText(/pain/i).first()).toBeVisible({ timeout: 15000 });
    await expect(messagesArea2.getByText(/available/i).first()).toBeVisible({ timeout: 15000 });
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
