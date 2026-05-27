import { useState } from 'react';
import FileUpload from './components/FileUpload';
import ChapterList from './components/ChapterList';
import TextReview from './components/TextReview';
import QuizViewer from './components/QuizViewer';

function App() {
  const [course, setCourse] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [extractedText, setExtractedText] = useState('');
  const [quiz, setQuiz] = useState(null);
  const [selectedChapterNumber, setSelectedChapterNumber] = useState(null);
  const [selectedChapterId, setSelectedChapterId] = useState(null);
  const [quizSettings, setQuizSettings] = useState({ difficulty: 'medium', questionTypes: ['mcq'] });

  const handleMaterialReady = (data) => {
    setCourse({
      id: data.document_id,
      title: data.book,
      status: data.status,
    });
    setChapters(data.chapters || []);
    setExtractedText(data.extracted_text || (data.chapters || []).map((chapter) => chapter.content || '').join('\n\n'));
    setQuiz(null);
    setSelectedChapterNumber(null);
    setSelectedChapterId(null);
  };

  return (
    <main className="min-h-screen bg-[#f6f7f1] text-[#1f2933]">
      <section className="border-b border-[#d9ded2] bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-5 px-5 py-8 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-[#4f6f52]">
              Study material to practice quiz
            </p>
            <h1 className="mt-2 text-3xl font-bold md:text-4xl">LearnMate Quiz Studio</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#55616c]">
              Upload PDF or DOCX notes, review detected chapters, and generate short
              revision quizzes for focused practice.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 rounded-lg border border-[#d9ded2] bg-[#fbfcf8] p-3 text-center">
            <div>
              <div className="text-xl font-bold">{chapters.length}</div>
              <div className="text-xs text-[#6b7280]">chapters</div>
            </div>
            <div>
              <div className="text-xl font-bold">{quiz?.questions?.length || 0}</div>
              <div className="text-xs text-[#6b7280]">questions</div>
            </div>
            <div>
              <div className="text-xl font-bold">{course ? '1' : '0'}</div>
              <div className="text-xs text-[#6b7280]">file</div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-5 px-5 py-6 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-5">
          <FileUpload onChaptersDetected={handleMaterialReady} />
          {course && (
            <div className="rounded-lg border border-[#d9ded2] bg-white p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#6b7280]">
                Active material
              </p>
              <h2 className="mt-1 break-words text-lg font-semibold">{course.title}</h2>
              <p className="mt-2 text-sm text-[#55616c]">
                Status: {course.status === 'existing' ? 'Loaded from saved analysis' : 'Freshly processed'}
              </p>
            </div>
          )}
        </aside>

        <div className="space-y-5">
          {chapters.length === 0 && (
            <div className="rounded-lg border border-dashed border-[#b9c3b1] bg-white p-8 text-center">
              <h2 className="text-xl font-semibold">Start with your study file</h2>
              <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-[#55616c]">
                The chapter panel appears after upload. Choose any chapter to create
                a five-question practice set.
              </p>
            </div>
          )}

          {chapters.length > 0 && (
            <>
              <TextReview
                course={course}
                extractedText={extractedText}
                onRevisionReady={(data) => {
                  setChapters(data.chapters || []);
                  setExtractedText(data.extracted_text || '');
                  setQuiz(null);
                  setSelectedChapterNumber(null);
                  setSelectedChapterId(null);
                }}
              />
              <ChapterList
                book={course?.title}
                documentId={course?.id}
                chapters={chapters}
                onQuizReady={(quizData, chapterNum, chapterId, settings) => {
                  setQuiz(quizData);
                  setSelectedChapterNumber(chapterNum);
                  setSelectedChapterId(chapterId);
                  setQuizSettings(settings || { difficulty: 'medium', questionTypes: ['mcq'] });
                }}
              />
            </>
          )}

          {quiz && (
            <QuizViewer
              quiz={quiz}
              chapterNumber={selectedChapterNumber}
              chapterId={selectedChapterId}
              documentId={course?.id}
              book={course?.title}
              quizSettings={quizSettings}
            />
          )}
        </div>
      </section>
    </main>
  );
}

export default App;
