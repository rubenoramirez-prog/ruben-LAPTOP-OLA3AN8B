import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const DRIVER_PATH = path.join(__dirname, 'humanize_driver.py');

test.describe('Instagram Humanizer Validation', () => {

  test('should significantly increase human score for AI-slop text', async () => {
    // Run driver with a prompt that generates highly mechanical text
    execSync(`python "${DRIVER_PATH}" "BAD prompt"`);

    const output = JSON.parse(fs.readFileSync('humanize_test_output.json', 'utf8'));

    const rawScore = output.raw.score;
    const cleanScore = output.clean.score;
    const delta = output.delta;

    // Rule 1: The human score must improve
    expect(delta).toBeGreaterThan(0);

    // Rule 2: Fingerprint check (The most mechanical tell)
    // In a "BAD" prompt, the raw fingerprint should be low, and clean should be much higher
    expect(output.clean.checks.FINGERPRINT.score).toBeGreaterThan(output.raw.checks.FINGERPRINT.score);

    // Rule 3: Slop Density check
    // Lexical slop (like "delve") should be reduced
    expect(output.clean.checks["SLOP DENSITY"].score).toBeGreaterThan(output.raw.checks["SLOP DENSITY"].score);

    // Rule 4: Verify a specific "slop" word was removed
    const rawText = output.raw.text.toLowerCase();
    const cleanText = output.clean.text.toLowerCase();

    if (rawText.includes('delve')) {
      expect(cleanText).not.toContain('delve');
    }
  });

  test('should not degrade a text that is already human', async () => {
    execSync(`python "${DRIVER_PATH}" "GOOD prompt"`);

    const output = JSON.parse(fs.readFileSync('humanize_test_output.json', 'utf8'));

    // A human text should stay human or improve slightly, not crash
    expect(output.clean.score).toBeGreaterThanOrEqual(output.raw.score - 5);
  });

});
