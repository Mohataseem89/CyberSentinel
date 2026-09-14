import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import ScannerPage from './ScannerPage';
vi.mock('../services/api', () => ({ analyzeURL: vi.fn() }));

test('shows accessible validation before a request', () => {
  render(<ScannerPage />);
  fireEvent.click(screen.getByRole('button', { name: /check link/i }));
  expect(screen.getByRole('alert')).toHaveTextContent(/complete HTTP or HTTPS URL/i);
});
