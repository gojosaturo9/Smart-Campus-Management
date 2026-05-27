import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function TextReview({ course, extractedText, onRevisionReady }) {
  const [text, setText] = useState(extractedText || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const hasUnsavedChanges = text !== (extractedText || '');

  useEffect(() => {
    setText(extractedText || '');
  }, [extractedText]);

  useEffect(() => {
    const handleBeforeUnload = (event) => {
      if (!hasUnsavedChanges) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  if (!course?.id) return null;

  const applyText = async () => {
    setSaving(true);
    setError('');
    try {
      const response = await axios.put(
        `${API_BASE}/documents/${course.id}/chapters-from-text`,
        { text },
      );
      onRevisionReady(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not apply edited text.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="rounded-lg border border-[#d9ded2] bg-white">
      <div className="border-b border-[#e6eadf] px-5 py-4">
        <h2 className="text-lg font-semibold">Review extracted text</h2>
        <p className="text-sm text-[#6b7280]">
          Clean OCR mistakes here before generating quizzes. Better text gives better MCQs.
        </p>
      </div>

      <div className="px-5 py-4">
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={12}
          className="w-full rounded-md border border-[#cfd7c6] bg-[#fbfcf8] p-3 text-sm leading-6 outline-none focus:border-[#304c3a]"
        />
        {error && <p className="mt-3 rounded bg-[#fff1f0] p-3 text-sm text-[#b42318]">{error}</p>}
        <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <p className="text-xs text-[#6b7280]">
            {text.trim().split(/\s+/).filter(Boolean).length} words
            {hasUnsavedChanges ? ' - unsaved changes' : ''}
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setText(extractedText || '')}
              disabled={saving || !hasUnsavedChanges}
              className="h-10 rounded-md border border-[#304c3a] px-4 text-sm font-semibold text-[#304c3a] transition hover:bg-[#eef5ea] disabled:cursor-not-allowed disabled:opacity-60"
            >
              Reset
            </button>
            <button
              type="button"
              onClick={applyText}
              disabled={saving || !hasUnsavedChanges || text.trim().length < 30}
              className="h-10 rounded-md bg-[#304c3a] px-4 text-sm font-semibold text-white transition hover:bg-[#24392c] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
