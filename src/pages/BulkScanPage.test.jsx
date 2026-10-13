import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { vi } from 'vitest';

import BulkScanPage from './BulkScanPage';
import { getBulkJob } from '../services/api';

vi.mock('../services/api', () => ({
  createBulkJob: vi.fn(),

  listBulkJobs: vi.fn().mockResolvedValue({
    jobs: [
      {
        id: 'job-1',
        status: 'COMPLETED',
        processed: 2,
        total: 2,
        progress_percent: 100,
      },
    ],
  }),

  getBulkJob: vi.fn().mockResolvedValue({
    job: {
      id: 'job-1',
      status: 'COMPLETED',
      processed: 2,
      total: 2,
      successful: 2,
      failed: 0,
    },

    results: [
      {
        row: 2,
        url: 'https://safe.example/…',
        verdict: 'Safe',
        threat_score: 3,
        status: 'COMPLETED',
        error: null,
      },
      {
        row: 3,
        url: 'https://bad.example/…',
        verdict: 'Dangerous',
        threat_score: 90,
        status: 'COMPLETED',
        error: null,
      },
    ],

    pagination: {
      page: 1,
      per_page: 100,
      total_items: 2,
      total_pages: 1,
      has_previous: false,
      has_next: false,
    },
  }),

  cancelBulkJob: vi.fn(),
  downloadBulkResults: vi.fn(),
}));

test(
  'renders structured bulk results and requests verdict filters server-side',
  async () => {
    render(<BulkScanPage />);

    fireEvent.click(
      await screen.findByRole('button', {
        name: /COMPLETED.*job-1/i,
      }),
    );

    expect(
      await screen.findByRole('columnheader', {
        name: 'Verdict',
      }),
    ).toBeInTheDocument();

    // Verify that the Dangerous verdict exists specifically
    // inside the results table rather than matching the
    // Dangerous filter button.
    const table = screen.getByRole('table');

    expect(
      within(table).getByText('Dangerous'),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Safe',
      }),
    );

    await waitFor(() =>
      expect(getBulkJob).toHaveBeenLastCalledWith(
        'job-1',
        {
          page: 1,
          perPage: 100,
          verdict: 'Safe',
        },
      ),
    );
  },
);