import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FileScanPage from './FileScanPage';
import {
  createFileScan,
  getFileScanCapabilities,
  listFileScans,
} from '../services/api';

vi.mock('../services/api', () => ({
  createFileScan: vi.fn(),
  getFileScanCapabilities: vi.fn(),
  listFileScans: vi.fn(),
}));

describe('FileScanPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    getFileScanCapabilities.mockResolvedValue({
      enabled: true,
      max_bytes: 10 * 1024 * 1024,
      allowed_types: [
        'html',
        'text',
        'pdf',
        'png',
        'jpeg',
        'gif',
      ],
      archives_supported: false,
      consent_required: true,
    });

    listFileScans.mockResolvedValue({
      jobs: [],
    });

    createFileScan.mockResolvedValue({
      job: {
        id: 'scan-1',
      },
    });
  });

  it('shows limited-confidence wording for static-only results', async () => {
    listFileScans.mockResolvedValue({
      jobs: [
        {
          id: 'scan-1',
          status: 'COMPLETED',
          file_name: 'example.txt',
          file_type: 'text',
          mime_type: 'text/plain',
          size_bytes: 100,
          verdict: 'CLEAN_CHECKS_COMPLETED',
          malware_status: 'static_checks_only',
          error_code: 'malware_reputation_unavailable',
          indicators: [],
          created_at: '2026-10-16T12:00:00',
        },
      ],
    });

    render(<FileScanPage />);

    expect(
      await screen.findByText(
        'No suspicious indicators found',
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /malware reputation was unavailable or the file hash was unknown/i,
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /does not guarantee that the file is safe/i,
      ),
    ).toBeInTheDocument();
  });

  it('requires consent before submitting a file', async () => {
    render(<FileScanPage />);

    await screen.findByText(
      /supported:/i,
    );

    const input = screen.getByLabelText(
      'Choose file to analyze',
    );

    const file = new File(
      ['hello'],
      'example.txt',
      {
        type: 'text/plain',
      },
    );

    fireEvent.change(
      input,
      {
        target: {
          files: [file],
        },
      },
    );

    const button = screen.getByRole(
      'button',
      {
        name: 'Analyze file',
      },
    );

    expect(button).toBeDisabled();

    const checkbox = screen.getByRole(
      'checkbox',
    );

    fireEvent.click(
      checkbox,
    );

    expect(button).toBeEnabled();

    fireEvent.click(
      button,
    );

    await waitFor(() => {
      expect(
        createFileScan,
      ).toHaveBeenCalledWith(
        file,
        true,
      );
    });
  });

  it('shows threat results without calling them safe', async () => {
    listFileScans.mockResolvedValue({
      jobs: [
        {
          id: 'scan-threat',
          status: 'COMPLETED',
          file_name: 'suspicious.pdf',
          file_type: 'pdf',
          mime_type: 'application/pdf',
          size_bytes: 1024,
          verdict: 'THREAT_DETECTED',
          malware_status: 'malware_detected',
          error_code: null,
          indicators: [
            {
              code: 'file_hash_reputation_detection',
              severity: 'high',
              detections: 12,
              vendors: 70,
            },
          ],
          created_at: '2026-10-16T12:00:00',
        },
      ],
    });

    render(<FileScanPage />);

    expect(
      await screen.findByText(
        'Threat detected',
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /threat evidence was detected/i,
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /reputation detections: 12 \/ 70/i,
      ),
    ).toBeInTheDocument();
  });
});