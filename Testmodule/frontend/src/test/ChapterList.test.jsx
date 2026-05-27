import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChapterList from '../components/ChapterList';

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
  },
}));

import axios from 'axios';

const SAMPLE_CHAPTERS = [
  { id: 11, chapter_title: 'Introduction', title: 'Introduction' },
  { id: 12, chapter_title: 'Chapter 1', title: 'Chapter 1' },
];

describe('ChapterList', () => {
  let onQuizReady;

  beforeEach(() => {
    onQuizReady = vi.fn();
    vi.clearAllMocks();
  });

  it('renders all chapter titles', () => {
    render(
      <ChapterList book="TestBook" documentId={7} chapters={SAMPLE_CHAPTERS} onQuizReady={onQuizReady} />
    );
    expect(screen.getByText('Introduction')).toBeInTheDocument();
    expect(screen.getByText('Chapter 1')).toBeInTheDocument();
  });

  it('renders a Generate Quiz button for each chapter', () => {
    render(
      <ChapterList book="TestBook" chapters={SAMPLE_CHAPTERS} onQuizReady={onQuizReady} />
    );
    const buttons = screen.getAllByRole('button', { name: /generate quiz/i });
    expect(buttons).toHaveLength(SAMPLE_CHAPTERS.length);
  });

  it('calls onQuizReady with quiz data when quiz generation succeeds', async () => {
    const quizData = { chapter_id: 1, questions: [] };
    axios.post.mockResolvedValueOnce({ data: quizData });

    render(
      <ChapterList book="TestBook" chapters={SAMPLE_CHAPTERS} onQuizReady={onQuizReady} />
    );

    fireEvent.click(screen.getAllByRole('button', { name: /generate quiz/i })[0]);

    await waitFor(() => {
      expect(onQuizReady).toHaveBeenCalledWith(
        quizData,
        1,
        11,
        { difficulty: 'medium', questionTypes: ['mcq'] },
      );
    });
  });

  it('shows error message when quiz generation fails', async () => {
    axios.post.mockRejectedValueOnce({
      response: { data: { detail: 'Server error' } },
    });

    render(
      <ChapterList book="TestBook" chapters={SAMPLE_CHAPTERS} onQuizReady={onQuizReady} />
    );

    fireEvent.click(screen.getAllByRole('button', { name: /generate quiz/i })[0]);

    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
    });
  });
});
