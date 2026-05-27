import { useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function ChapterList({ book, documentId, chapters, onQuizReady }) {
  const [loadingChapterIndex, setLoadingChapterIndex] = useState(null);
  const [error, setError] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [questionTypes, setQuestionTypes] = useState(['mcq']);

  const toggleQuestionType = (type) => {
    setQuestionTypes((current) => {
      if (current.includes(type) && current.length > 1) {
        return current.filter((item) => item !== type);
      }
      if (!current.includes(type)) return [...current, type];
      return current;
    });
  };

  const generateQuiz = async (chapterIndex) => {
    setLoadingChapterIndex(chapterIndex);
    setError('');

    try {
      const chapter = chapters[chapterIndex];
      const chapterId = chapter.id;
      const params = new URLSearchParams({
        difficulty,
        question_types: questionTypes.join(','),
      });
      const url = documentId && chapterId
        ? `${API_BASE}/documents/${documentId}/chapters/${chapterId}/quiz?${params.toString()}`
        : `${API_BASE}/generate-quiz/?book=${encodeURIComponent(book)}&chapter_number=${chapterIndex + 1}&${params.toString()}`;
      const response = await axios.post(url);
      onQuizReady(response.data, chapterIndex + 1, chapterId, { difficulty, questionTypes });
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not generate a practice set.');
    } finally {
      setLoadingChapterIndex(null);
    }
  };

  return (
    <section className="rounded-lg border border-[#d9ded2] bg-white">
      <div className="flex items-center justify-between border-b border-[#e6eadf] px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold">Detected chapters</h2>
          <p className="text-sm text-[#6b7280]">Select a chapter to build a revision quiz.</p>
        </div>
        <span className="rounded-full bg-[#eef5ea] px-3 py-1 text-sm font-semibold text-[#304c3a]">
          {chapters.length}
        </span>
      </div>

      <div className="grid gap-4 border-b border-[#e6eadf] px-5 py-4 md:grid-cols-[1fr_1fr]">
        <label className="text-sm font-medium text-[#334155]">
          Difficulty
          <select
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
            className="mt-2 h-10 w-full rounded-md border border-[#cfd7c6] bg-white px-3 text-sm outline-none focus:border-[#304c3a]"
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>
        <fieldset>
          <legend className="text-sm font-medium text-[#334155]">Question types</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {[
              ['mcq', 'MCQ'],
              ['short_answer', 'Short answer'],
              ['true_false', 'True/False'],
            ].map(([value, label]) => (
              <label key={value} className="flex h-10 items-center gap-2 rounded-md border border-[#cfd7c6] bg-white px-3 text-sm">
                <input
                  type="checkbox"
                  checked={questionTypes.includes(value)}
                  onChange={() => toggleQuestionType(value)}
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>
      </div>

      {error && <p className="mx-5 mt-4 rounded bg-[#fff1f0] p-3 text-sm text-[#b42318]">{error}</p>}

      <div className="divide-y divide-[#edf0e8]">
        {chapters.map((chapter, index) => {
          const title = chapter.chapter_title || chapter.title || `Chapter ${index + 1}`;
          const isLoading = loadingChapterIndex === index;

          return (
            <div key={`${title}-${index}`} className="grid gap-3 px-5 py-4 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <p className="text-sm font-semibold text-[#6b7280]">Section {index + 1}</p>
                <h3 className="mt-1 break-words font-medium text-[#1f2933]">{title}</h3>
              </div>
              <button
                type="button"
                onClick={() => generateQuiz(index)}
                className="h-10 rounded-md bg-[#304c3a] px-4 text-sm font-semibold text-white transition hover:bg-[#24392c] disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loadingChapterIndex !== null}
              >
                {isLoading ? 'Creating...' : 'Generate Quiz'}
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}
