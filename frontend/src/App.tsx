import { useState } from 'react';
import { api } from './api/client';
import type { Project, QuestionAnswerBundle, RfpQuestion } from './types';

export function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [questions, setQuestions] = useState<RfpQuestion[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<RfpQuestion | null>(null);
  const [bundle, setBundle] = useState<QuestionAnswerBundle | null>(null);
  const [finalText, setFinalText] = useState('');
  const [message, setMessage] = useState('');

  async function createDemoProject() {
    const created = await api.create_project({ name: 'City Hospital RFP', client_name: 'City Hospital' });
    setProject(created);
    setMessage('Project created. Upload sample files next.');
  }

  async function handleRfpUpload(file: File) {
    if (!project) return;
    await api.upload_rfp_document(project.id, file);
    setMessage('RFP uploaded.');
  }

  async function handleKnowledgeUpload(file: File) {
    if (!project) return;
    await api.upload_knowledge_document(project.id, file);
    setMessage('Knowledge document uploaded and chunked.');
  }

  async function extractQuestions() {
    if (!project) return;
    const extracted = await api.extract_questions(project.id);
    setQuestions(extracted);
    setSelectedQuestion(extracted[0] ?? null);
    setMessage(`Extracted ${extracted.length} questions.`);
  }

  async function draftAnswer(question: RfpQuestion) {
    const response = await api.draft_answer(question.id);
    setBundle(response);
    setFinalText(response.answer.final_text);
    setSelectedQuestion(question);
  }

  async function saveAnswer() {
    if (!bundle) return;
    const updated = await api.update_answer(bundle.answer.id, { final_text: finalText });
    setBundle({ ...bundle, answer: updated as QuestionAnswerBundle['answer'] });
    setMessage('Answer saved as edited.');
  }

  async function approveAnswer() {
    if (!bundle) return;
    const updated = await api.approve_answer(bundle.answer.id);
    setBundle({ ...bundle, answer: updated as QuestionAnswerBundle['answer'] });
    setMessage('Answer approved.');
  }

  async function exportProject() {
    if (!project) return;
    const result = await api.export_project(project.id);
    setMessage(`Exported ${result.exported_answer_count} answers: ${result.download_url}`);
  }

  return (
    <main className="app-shell">
      <header>
        <p className="eyebrow">Hackathon MVP</p>
        <h1>RFP Copilot</h1>
        <p>Draft source-backed RFP answers and keep humans in control before export.</p>
      </header>

      <section className="panel">
        <h2>1. Project</h2>
        <button onClick={createDemoProject}>Create demo project</button>
        {project && <p>Active project: <strong>{project.name}</strong></p>}
      </section>

      <section className="grid">
        <div className="panel">
          <h2>2. Upload</h2>
          <label>
            RFP document
            <input type="file" onChange={(event) => event.target.files?.[0] && handleRfpUpload(event.target.files[0])} />
          </label>
          <label>
            Knowledge document
            <input type="file" onChange={(event) => event.target.files?.[0] && handleKnowledgeUpload(event.target.files[0])} />
          </label>
          <button disabled={!project} onClick={extractQuestions}>Extract questions</button>
        </div>

        <div className="panel">
          <h2>3. Questions</h2>
          <div className="question-list">
            {questions.map((question) => (
              <button
                key={question.id}
                className={selectedQuestion?.id === question.id ? 'selected' : ''}
                onClick={() => setSelectedQuestion(question)}
              >
                <span>{question.order_index + 1}. {question.question_text}</span>
                <small>{question.category} / {question.status}</small>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="grid wide">
        <div className="panel editor-panel">
          <h2>4. Review answer</h2>
          {selectedQuestion ? (
            <>
              <p className="question-text">{selectedQuestion.question_text}</p>
              <button onClick={() => draftAnswer(selectedQuestion)}>Draft answer</button>
              {bundle && (
                <>
                  {bundle.answer.warning && <p className="warning">{bundle.answer.warning}</p>}
                  <textarea value={finalText} onChange={(event) => setFinalText(event.target.value)} />
                  <div className="actions">
                    <button onClick={saveAnswer}>Save edit</button>
                    <button onClick={approveAnswer}>Approve</button>
                    <button onClick={() => bundle && api.flag_answer(bundle.answer.id, 'Needs review')}>Flag</button>
                    <button onClick={() => bundle && api.reject_answer(bundle.answer.id)}>Reject</button>
                  </div>
                  <p>Status: <strong>{bundle.answer.status}</strong></p>
                </>
              )}
            </>
          ) : (
            <p>Select a question first.</p>
          )}
        </div>

        <aside className="panel">
          <h2>Citations</h2>
          {bundle?.citations.length ? bundle.citations.map((citation) => (
            <article key={citation.id} className="citation">
              <strong>{citation.document_title}</strong>
              <p>{citation.excerpt}</p>
              <small>score: {citation.relevance_score ?? 'n/a'}</small>
            </article>
          )) : <p>No citations yet.</p>}
        </aside>
      </section>

      <section className="panel">
        <h2>5. Export</h2>
        <button disabled={!project} onClick={exportProject}>Export reviewed DOCX</button>
        {message && <p className="message">{message}</p>}
      </section>
    </main>
  );
}
