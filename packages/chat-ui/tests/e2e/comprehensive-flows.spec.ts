/**
 * Comprehensive E2E tests for PearlFlow full conversation flows
 * These tests verify complete end-to-end scenarios
 */

import { test, expect } from '@playwright/test';

test.describe('Full E2E - New Patient Triage to Booking Flow', () => {
  test('Complete triage and booking flow for new patient', async ({ page }) => {
    // Step 1: Open demo page and chat widget
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Step 2: Send initial pain message
    await input.fill('I have severe toothache');
    await sendButton.click();

    // Step 3: Wait for pain level question
    await expect(messagesArea.getByText(/pain level/i)).toBeVisible({ timeout: 15000 });

    // Step 4: Provide pain level
    await input.fill('8');
    await sendButton.click();

    // Step 5: Answer swelling question
    await expect(messagesArea.getByText(/swelling/i).first()).toBeVisible({ timeout: 10000 });
    await input.fill('No swelling');
    await sendButton.click();

    // Step 6: Answer fever question
    await expect(messagesArea.getByText(/fever/i).first()).toBeVisible({ timeout: 10000 });
    await input.fill('No fever');
    await sendButton.click();

    // Step 7: Verify priority score is assigned
    await expect(messagesArea.getByText(/priority/i)).toBeVisible({ timeout: 15000 });

    // Step 8: Verify booking offer appears
    await expect(messagesArea.getByText(/book/i)).toBeVisible({ timeout: 15000 });

    // Step 9: Verify the flow reaches booking stage
    const bookingRelated = await messagesArea.getByText(/slot|appointment|book/i).count();
    expect(bookingRelated).toBeGreaterThan(0);
  });
});

test.describe('Full E2E - Existing Patient Quick Booking Flow', () => {
  test('Quick booking for existing patient', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Request cleaning appointment
    await input.fill('I need to book a cleaning');
    await sendButton.click();

    // Verify booking flow activated
    await expect(messagesArea.getByText(/cleaning|appointment|book/i)).toBeVisible({ timeout: 15000 });

    // Provide phone number
    await input.fill('+61400000000');
    await sendButton.click();

    // Verify system processes the request
    await expect(messagesArea.locator('div').filter({ hasText: /book|slot|appointment/i }).first()).toBeVisible({ timeout: 15000 });
  });
});

test.describe('Full E2E - Emergency Triage Flow with Escalation', () => {
  test('Emergency triage with high priority escalation', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Report severe pain
    await input.fill('I have severe pain');
    await sendButton.click();

    // Pain level 10
    await expect(messagesArea.getByText(/pain level/i)).toBeVisible({ timeout: 15000 });
    await input.fill('10');
    await sendButton.click();

    // Report swelling
    await expect(messagesArea.getByText(/swelling/i).first()).toBeVisible({ timeout: 10000 });
    await input.fill('Yes, severe swelling');
    await sendButton.click();

    // Report fever
    await expect(messagesArea.getByText(/fever/i).first()).toBeVisible({ timeout: 10000 });
    await input.fill('Yes, high fever');
    await sendButton.click();

    // Verify high priority score
    await expect(messagesArea.getByText(/priority/i)).toBeVisible({ timeout: 15000 });

    // Verify emergency escalation
    const emergencyText = await messagesArea.getByText(/urgent|emergency|immediate/i).count();
    expect(emergencyText).toBeGreaterThan(0);

    // Verify earliest slot offer
    await expect(messagesArea.getByText(/slot|appointment|earliest/i)).toBeVisible({ timeout: 15000 });
  });
});

test.describe('Full E2E - Move Negotiation for High-Value Procedure', () => {
  test('Move negotiation flow for high-value procedure', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Request high-value procedure
    await input.fill('I need a crown procedure');
    await sendButton.click();

    // Verify move suggestion
    await expect(messagesArea.locator('div').filter({ hasText: /move|offer|incentive/i }).first()).toBeVisible({ timeout: 20000 });

    // Verify move suggestions generated
    const moveText = await messagesArea.getByText(/move|reschedule|incentive/i).count();
    expect(moveText).toBeGreaterThan(0);

    // Accept move offer
    await input.fill('I accept the move');
    await sendButton.click();

    // Verify incentive applied
    await expect(messagesArea.getByText(/discount|priority|incentive/i)).toBeVisible({ timeout: 15000 });

    // Verify booking confirmation
    await expect(messagesArea.getByText(/crown|booked|confirmed/i)).toBeVisible({ timeout: 15000 });
  });
});

test.describe('Full E2E - Session Recovery After Disconnect', () => {
  test('Session state recovery after browser close', async ({ page, context }) => {
    // Start conversation
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    const input = page.getByPlaceholder('Type a message...');
    const sendButton = page.getByRole('button', { name: 'Send message' });
    const messagesArea = page.locator('.pf-overflow-y-auto');

    // Complete partial triage
    await input.fill('I have toothache');
    await sendButton.click();
    await expect(messagesArea.getByText(/pain level/i)).toBeVisible({ timeout: 15000 });

    await input.fill('7');
    await sendButton.click();
    await expect(messagesArea.getByText(/swelling/i).first()).toBeVisible({ timeout: 10000 });

    // Simulate reconnection by opening new context
    const newContext = await context.browser().newContext();
    const newPage = await newContext.newPage();

    // Reopen with session
    await newPage.goto('/');
    await newPage.getByRole('button', { name: 'Open chat' }).click();

    // Verify conversation history preserved
    const newMessagesArea = newPage.locator('.pf-overflow-y-auto');
    await expect(newMessagesArea.getByText(/pain|swelling/i)).toBeVisible({ timeout: 15000 });

    // Continue from last point
    await newPage.getByPlaceholder('Type a message...').fill('No swelling');
    await newPage.getByRole('button', { name: 'Send message' }).click();

    // Verify can complete flow
    await expect(newMessagesArea.getByText(/fever|priority/i)).toBeVisible({ timeout: 15000 });

    await newContext.close();
  });
});

test.describe('Full E2E - Concurrent Sessions for Same Clinic', () => {
  test('Multiple concurrent sessions are isolated', async ({ page, context }) => {
    // Open first browser tab
    await page.goto('/');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    const input1 = page.getByPlaceholder('Type a message...');
    const sendButton1 = page.getByRole('button', { name: 'Send message' });
    const messagesArea1 = page.locator('.pf-overflow-y-auto');

    // Start first conversation
    await input1.fill('I have toothache');
    await sendButton1.click();
    await expect(messagesArea1.getByText(/pain level/i)).toBeVisible({ timeout: 15000 });

    // Open second browser tab
    const newContext = await context.browser().newContext();
    const page2 = await newContext.newPage();
    await page2.goto('/');
    await page2.getByRole('button', { name: 'Open chat' }).click();
    await expect(page2.getByRole('heading', { name: 'PearlFlow Assistant' })).toBeVisible();

    const input2 = page2.getByPlaceholder('Type a message...');
    const sendButton2 = page2.getByRole('button', { name: 'Send message' });
    const messagesArea2 = page2.locator('.pf-overflow-y-auto');

    // Start different conversation
    await input2.fill('I need to book a cleaning');
    await sendButton2.click();
    await expect(messagesArea2.getByText(/cleaning|book|appointment/i)).toBeVisible({ timeout: 15000 });

    // Verify sessions are isolated
    await expect(messagesArea1.getByText(/pain level/i)).toBeVisible();
    await expect(messagesArea2.getByText(/cleaning|book/i)).toBeVisible();

    // Complete both flows
    await input1.fill('8');
    await sendButton1.click();
    await expect(messagesArea1.getByText(/swelling/i)).toBeVisible({ timeout: 10000 });

    await input2.fill('+61400000000');
    await sendButton2.click();

    // Verify no cross-contamination
    const bookingInFirst = await messagesArea1.getByText(/cleaning/i).count();
    expect(bookingInFirst).toBe(0);

    const painInSecond = await messagesArea2.getByText(/toothache/i).count();
    expect(painInSecond).toBe(0);

    await newContext.close();
  });
});
