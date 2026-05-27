import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function QuizViewer({ quiz, chapterNumber, chapterId, documentId, book, quizSettings }) {
  const [visibleQuestions, setVisibleQuestions] = useState([]);
  const [userAnswers, setUserAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [loadingNewQuiz, setLoadingNewQuiz] = useState(false);
  const [error, setError] = useState('');
  const [scoreHistory, setScoreHistory] = useState([]);

  useEffect(() => {
    if (quiz?.questions?.length) {
      choosePracticeQuestions(quiz.questions);
    }
  }, [quiz]);

  useEffect(() => {
    const saved = window.localStorage.getItem('learnmate-score-history');
    setScoreHistory(saved ? JSON.parse(saved) : []);
  }, []);

  const choosePracticeQuestions = (questions) => {
    const selected = [...questions].sort(() => 0.5 - Math.random()).slice(0, 5);
    setVisibleQuestions(selected);
    setUserAnswers({});
    setSubmitted(false);
    setScore(0);
    setError('');
  };

  const handleAnswerChange = (questionIndex, answer) => {
    setUserAnswers((current) => ({
      ...current,
      [questionIndex]: answer,
    }));
  };

  const submitAnswers = () => {
    const total = visibleQuestions.reduce((count, question, index) => {
      const given = (userAnswers[index] || '').trim().toLowerCase();
      const expected = (question.answer || question.answer_text || '').trim().toLowerCase();
      return given && given === expected ? count + 1 : count;
    }, 0);

    setScore(total);
    setSubmitted(true);
    const entry = {
      id: Date.now(),
      book,
      chapterNumber,
      score: total,
      total: visibleQuestions.length,
      createdAt: new Date().toLocaleString(),
    };
    const nextHistory = [entry, ...scoreHistory].slice(0, 8);
    setScoreHistory(nextHistory);
    window.localStorage.setItem('learnmate-score-history', JSON.stringify(nextHistory));
  };

  const regenerateQuiz = async () => {
    if ((!book || chapterNumber == null) && (!documentId || !chapterId)) return;

    setLoadingNewQuiz(true);
    setError('');

    try {
      const params = new URLSearchParams({
        difficulty: quizSettings?.difficulty || 'medium',
        question_types: (quizSettings?.questionTypes || ['mcq']).join(','),
      });
      const url = documentId && chapterId
        ? `${API_BASE}/documents/${documentId}/chapters/${chapterId}/quiz?${params.toString()}`
        : `${API_BASE}/generate-quiz/?book=${encodeURIComponent(book)}&chapter_number=${chapterNumber}&${params.toString()}`;
      const response = await axios.post(url);
      choosePracticeQuestions(response.data.questions || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not refresh the practice set.');
    } finally {
      setLoadingNewQuiz(false);
    }
  };

  const retryWrongAnswers = () => {
    const wrongQuestions = visibleQuestions.filter((question, index) => {
      const given = (userAnswers[index] || '').trim().toLowerCase();
      const expected = (question.answer || question.answer_text || '').trim().toLowerCase();
      return given !== expected;
    });
    choosePracticeQuestions(wrongQuestions.length ? wrongQuestions : visibleQuestions);
  };

  const exportCsv = () => {
    const rows = [
      ['Question', 'Your Answer', 'Correct Answer', 'Result'],
      ...visibleQuestions.map((question, index) => {
        const correctAnswer = question.answer || question.answer_text || '';
        const userAnswer = userAnswers[index] || '';
        const isCorrect = userAnswer.trim().toLowerCase() === correctAnswer.trim().toLowerCase();
        return [question.question || question.question_text, userAnswer, correctAnswer, isCorrect ? 'Correct' : 'Needs review'];
      }),
    ];
    const csv = rows.map((row) => row.map((cell) => `"${String(cell || '').replaceAll('"', '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `learnmate-chapter-${chapterNumber || 'quiz'}-results.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="rounded-lg border border-[#d9ded2] bg-white">
      <div className="flex flex-col gap-3 border-b border-[#e6eadf] px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Generated Quiz</h2>
          <p className="text-sm text-[#6b7280]">Chapter {chapterNumber} practice set</p>
        </div>
        <button
          type="button"
          onClick={regenerateQuiz}
          disabled={loadingNewQuiz}
          className="h-10 rounded-md border border-[#304c3a] px-4 text-sm font-semibold text-[#304c3a] transition hover:bg-[#eef5ea] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loadingNewQuiz ? 'Refreshing...' : 'Generate New Quiz'}
        </button>
      </div>

      {error && <p className="mx-5 mt-4 rounded bg-[#fff1f0] p-3 text-sm text-[#b42318]">{error}</p>}

      <div className="space-y-4 px-5 py-5">
        {visibleQuestions.map((question, index) => {
          const questionText = question.question || question.question_text;
          const questionType = question.type || question.question_type || 'question';
          const correctAnswer = question.answer || question.answer_text || '';
          const userAnswer = userAnswers[index] || '';
          const isCorrect = userAnswer.trim().toLowerCase() === correctAnswer.trim().toLowerCase();
          const options = question.options || (questionType === 'true_false' ? ['True', 'False'] : []);

          return (
            <article
              key={`${questionText}-${index}`}
              className={`rounded-lg border p-4 ${
                submitted ? (isCorrect ? 'border-[#2f855a] bg-[#f0fff4]' : 'border-[#c2410c] bg-[#fff7ed]') : 'border-[#e1e6db] bg-[#fbfcf8]'
              }`}
            >
              <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <h3 className="font-semibold leading-6">
                  {index + 1}. {questionText}
                </h3>
                <span className="w-fit rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase text-[#55616c]">
                  {questionType}
                </span>
              </div>

              {options.length > 0 ? (
                <div className="mt-3 grid gap-2">
                {options.map((option) => (
                  <label key={option} className="flex items-center gap-2 rounded-md border border-[#e1e6db] bg-white p-3 text-sm">
                    <input
                      type="radio"
                      name={`question-${index}`}
                      value={option}
                      checked={userAnswer === option}
                      disabled={submitted}
                      onChange={() => handleAnswerChange(index, option)}
                    />
                    <span>{option}</span>
                  </label>
                ))}
                </div>
              ) : (
                <textarea
                  value={userAnswer}
                  disabled={submitted}
                  onChange={(event) => handleAnswerChange(index, event.target.value)}
                  rows={3}
                  className="mt-3 w-full rounded-md border border-[#e1e6db] bg-white p-3 text-sm outline-none focus:border-[#304c3a] disabled:opacity-70"
                  placeholder="Write your answer"
                />
              )}

              {submitted && (
                <div className="mt-3 text-sm font-medium text-[#334155]">
                  Result: {isCorrect ? 'Correct' : 'Needs review'}
                  <div className="mt-1 text-[#55616c]">Answer: {correctAnswer}</div>
                  {question.explanation && <div className="mt-1 text-[#55616c]">Explanation: {question.explanation}</div>}
                </div>
              )}
            </article>
          );
        })}
      </div>

      <div className="flex flex-col gap-3 border-t border-[#e6eadf] px-5 py-4 md:flex-row md:items-center md:justify-between">
        {!submitted ? (
          <button
            type="button"
            onClick={submitAnswers}
            disabled={visibleQuestions.length === 0}
            className="h-10 rounded-md bg-[#304c3a] px-5 text-sm font-semibold text-white transition hover:bg-[#24392c] disabled:cursor-not-allowed disabled:opacity-60"
          >
            Submit
          </button>
        ) : (
          <>
            <p className="text-lg font-bold text-[#304c3a]">
              Your Score: {score} / {visibleQuestions.length}
            </p>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={retryWrongAnswers} className="h-10 rounded-md border border-[#304c3a] px-4 text-sm font-semibold text-[#304c3a]">
                Retry Wrong Answers
              </button>
              <button type="button" onClick={exportCsv} className="h-10 rounded-md border border-[#304c3a] px-4 text-sm font-semibold text-[#304c3a]">
                Export CSV
              </button>
              <button type="button" onClick={() => window.print()} className="h-10 rounded-md border border-[#304c3a] px-4 text-sm font-semibold text-[#304c3a]">
                Export PDF
              </button>
            </div>
          </>
        )}
      </div>

      {scoreHistory.length > 0 && (
        <div className="border-t border-[#e6eadf] px-5 py-4">
          <h3 className="text-sm font-semibold text-[#334155]">Recent scores</h3>
          <div className="mt-3 grid gap-2">
            {scoreHistory.map((entry) => (
              <div key={entry.id} className="flex items-center justify-between rounded-md bg-[#fbfcf8] px-3 py-2 text-sm">
                <span>Chapter {entry.chapterNumber || '-'}</span>
                <span className="font-semibold">{entry.score}/{entry.total}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
