# LearnMate Quiz Studio Frontend

React/Vite UI for uploading study material, reviewing detected chapters, generating quiz sets, and checking answers.

## Stack

- React for component-based UI state.
- Vite for fast local development and production builds.
- Tailwind CSS for utility-first styling.
- Axios for backend API calls.
- React Dropzone for drag-and-drop uploads.
- Vitest and Testing Library for component tests.

## Setup

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:8000` in `.env`.

## Tests

```bash
npm test
```

## Main Files

- `src/App.jsx`: Dashboard layout and app-level state.
- `src/components/FileUpload.jsx`: PDF/DOCX upload panel.
- `src/components/ChapterList.jsx`: Chapter list and quiz generation trigger.
- `src/components/QuizViewer.jsx`: Quiz attempt, scoring, and refresh flow.
