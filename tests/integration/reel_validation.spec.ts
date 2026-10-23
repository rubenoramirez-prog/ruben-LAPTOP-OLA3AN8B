import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const DRIVER_PATH = path.join(__dirname, 'reel_driver.py');

test.describe('Instagram Reel Brand Validation', () => {

  test('should PASS when hookscore.py marks it as STRONG', async () => {
    execSync(`python "${DRIVER_PATH}" "GOOD prompt"`);

    const output = JSON.parse(fs.readFileSync('test_output.json', 'utf8'));

    // Validate using the real production threshold
    expect(output.score).toBeGreaterThanOrEqual(70);
    expect(output.verdict).toBe('STRONG');

    // Ensure "A Tu Marca" brand guidelines are still met
    const onScreenWords = output.hook_on_screen.split(' ').length;
    expect(onScreenWords).toBeLessThanOrEqual(6);

    const guruWords = ['unlock your potential', 'secret hack', 'game changer', 'hello everyone'];
    const scriptLower = output.script.toLowerCase();
    guruWords.forEach(word => {
      expect(scriptLower).not.toContain(word);
    });
  });

  test('should FAIL when hookscore.py marks it as WEAK', async () => {
    execSync(`python "${DRIVER_PATH}" "BAD prompt"`);

    const output = JSON.parse(fs.readFileSync('test_output.json', 'utf8'));

    // The real hookscore logic should mark this as WEAK or OK
    expect(output.score).toBeLessThan(70);
    expect(output.verdict).not.toBe('STRONG');

    // Verify the "Dealbreakers" (Greetings, Preambles) are caught
    expect(output.flags.length).toBeGreaterThan(0);
  });

});
