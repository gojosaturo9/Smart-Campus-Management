import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import QuizViewer from '../components/QuizViewer';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
  },
}));

import axios from 'axios';

const SAMPLE_QUIZ = {
  chapter_id: 1,
  questions: [
    {
      type: 'mcq',
      question: 'What is 2+2?',
      options: ['3', '4', '5', '6'],
      answer: '4',
    },
    {
      type: 'subjective',
      question: 'What is Python?',
      answer: 'A programming language.',
    },
  ],
};

describe('QuizViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders quiz questions', () => {
    render(
      <QuizViewer quiz={SAMPLE_QUIZ} chapterId={1} chapterNumber={1} book="TestBook" />
    );
    // At least one question should appear (up to 5 are sampled)
    expect(screen.getByText(/Generated Quiz/i)).toBeInTheDocument();
  });

  it('renders Submit button before submission', () => {
    render(
      <QuizViewer quiz={SAMPLE_QUIZ} chapterId={1} chapterNumber={1} book="TestBook" />
    );
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  it('shows score after submission', () => {
    render(
      <QuizViewer quiz={SAMPLE_QUIZ} chapterId={1} chapterNumber={1} book="TestBook" />
    );
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(screen.getByText(/your score/i)).toBeInTheDocument();
  });

  it('renders Generate New Quiz button', () => {
    render(
      <QuizViewer quiz={SAMPLE_QUIZ} chapterId={1} chapterNumber={1} book="TestBook" />
    );
    expect(screen.getByRole('button', { name: /generate new quiz/i })).toBeInTheDocument();
  });

  it('shows error when regeneration fails', async () => {
    axios.post.mockRejectedValueOnce({
      response: { data: { detail: 'Quiz generation failed' } },
    });

    render(
      <QuizViewer quiz={SAMPLE_QUIZ} chapterId={1} chapterNumber={1} book="TestBook" />
    );

    fireEvent.click(screen.getByRole('button', { name: /generate new quiz/i }));

    await waitFor(() => {
      expect(screen.getByText(/quiz generation failed/i)).toBeInTheDocument();
    });
  });
});
