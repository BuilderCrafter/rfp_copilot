import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from './api/client';
import { NewProjectModal } from './NewProjectModal';
import type {
  AnswerStatus,
  Project,
  QuestionAnswerBundle,
  QuestionStatus,
  RfpAssessment,
  RfpQuestion,
} from './types';

function statusTagClass(status: QuestionStatus | AnswerStatus): string {
  switch (status) {
    case 'approved':
      return 'tag tag-approved';
    case 'flagged':
    case 'rejected':
      return 'tag tag-flagged';
    case 'drafted':
    case 'edited':
      return 'tag tag-draft';
    case 'pending':
    case 'not_started':
      return 'tag tag-status';
    default: {
      const exhaustiveCheck: never = status;
      return exhaustiveCheck;
    }
  }
}

function trustScoreClass(score: number | null): string {
  if (score === null) return 'trust-score none';
  if (score >= 0.75) return 'trust-score high';
  if (score >= 0.5) return 'trust-score medium';
  return 'trust-score low';
}

function formatTrustScore(score: number | null): string {
  if (score === null) return '—';
  return `${Math.round(score * 100)}%`;
}

function topTrustScore(citations: QuestionAnswerBundle['citations']): number | null {
  if (!citations.length) return null;
  const scores = citations
    .map((citation) => citation.relevance_score)
    .filter((score): score is number => score !== null);
  return scores.length ? Math.max(...scores) : null;
}

type IntakeResult = {
  id: string;
  fileName: string;
  project: Project | null;
  assessment: RfpAssessment | null;
  error: string | null;
};

function formatProjectDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(new Date(value));
}

function humanizeStatus(value: string): string {
  return value.replace(/_/g, ' ');
}

function recommendationClass(recommendation: RfpAssessment['recommendation']): string {
  switch (recommendation) {
    case 'bid':
      return 'assessment-badge assessment-bid';
    case 'no_bid':
      return 'assessment-badge assessment-no-bid';
    case 'needs_review':
      return 'assessment-badge assessment-review';
    default: {
      const exhaustiveCheck: never = recommendation;
      return exhaustiveCheck;
    }
  }
}

function severityClass(severity: string): string {
  return `check-severity check-severity-${severity.replace(/_/g, '-')}`;
}

function bidderQuestions(assessment: RfpAssessment): string[] {
  const missingInfoQuestions = assessment.missing_information.map((item) => item.requested_action);
  const followUpQuestions = assessment.checklist
    .map((item) => item.follow_up)
    .filter((item): item is string => Boolean(item));

  return [...missingInfoQuestions, ...followUpQuestions].slice(0, 4);
}

function triageFlags(assessment: RfpAssessment): string[] {
  return assessment.bid_factors
    .filter((factor) => factor.sentiment !== 'positive')
    .map((factor) => factor.label)
    .slice(0, 4);
}

function TrustRing({ score }: { score: number | null }) {
  const pct = score === null ? 0 : Math.round(score * 100);
  const dash = score === null ? 0 : score * 62.8;

  return (
    <div className="trust-ring" aria-label={score === null ? 'No trust score' : `Trust ${pct}%`}>
      <svg viewBox="0 0 24 24" className="trust-ring-svg">
        <circle className="trust-ring-track" cx="12" cy="12" r="10" />
        <circle
          className={`trust-ring-fill ${trustScoreClass(score).replace('trust-score ', '')}`}
          cx="12"
          cy="12"
          r="10"
          strokeDasharray={`${dash} 62.8`}
        />
      </svg>
      <span className="trust-ring-label">{formatTrustScore(score)}</span>
    </div>
  );
}

export function App() {
  const desktopRef = useRef<HTMLDivElement>(null);
  const intakeRfpInputRef = useRef<HTMLInputElement>(null);
  const rfpInputRef = useRef<HTMLInputElement>(null);
  const backgroundAudioRef = useRef<HTMLAudioElement>(null);
  const gondorAudioRef = useRef<HTMLAudioElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioSourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const audioAnalyserRef = useRef<AnalyserNode | null>(null);
  const audioDataRef = useRef<Uint8Array<ArrayBuffer> | null>(null);
  const discoFrameRef = useRef<number | null>(null);
  const resumeBackgroundAfterGondorRef = useRef(false);
  const hasUserPausedBackgroundRef = useRef(false);
  const [project, setProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [questions, setQuestions] = useState<RfpQuestion[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<RfpQuestion | null>(null);
  const [bundle, setBundle] = useState<QuestionAnswerBundle | null>(null);
  const [answerByQuestion, setAnswerByQuestion] = useState<Record<string, QuestionAnswerBundle>>({});
  const [finalText, setFinalText] = useState('');
  const [message, setMessage] = useState('');
  const [messageIsError, setMessageIsError] = useState(false);
  const [intakeResults, setIntakeResults] = useState<IntakeResult[]>([]);
  const [isProcessingIntake, setIsProcessingIntake] = useState(false);
  const [isUploadingRfp, setIsUploadingRfp] = useState(false);
  const [hasRfpDocument, setHasRfpDocument] = useState(false);
  const [isBackgroundMusicPlaying, setIsBackgroundMusicPlaying] = useState(false);
  const [isDiscoActive, setIsDiscoActive] = useState(false);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('City Hospital RFP');
  const [newClientName, setNewClientName] = useState('City Hospital');
  const [modalError, setModalError] = useState('');

  const approvedCount = questions.filter((question) => question.status === 'approved').length;
  const progressPct = questions.length ? Math.round((approvedCount / questions.length) * 100) : 0;
  const sortedProjects = useMemo(
    () =>
      [...projects].sort(
        (first, second) =>
          new Date(second.updated_at).getTime() - new Date(first.updated_at).getTime(),
      ),
    [projects],
  );

  const selectedBundle = useMemo(() => {
    if (!selectedQuestion) return null;
    if (selectedQuestion.id === bundle?.question_id) return bundle;
    return answerByQuestion[selectedQuestion.id] ?? null;
  }, [answerByQuestion, bundle, selectedQuestion]);

  function resetWorkspace() {
    setQuestions([]);
    setSelectedQuestion(null);
    setBundle(null);
    setAnswerByQuestion({});
    setFinalText('');
    setHasRfpDocument(false);
  }

  function showMessage(text: string, isError = false) {
    setMessage(text);
    setMessageIsError(isError);
  }

  function stopDiscoLights() {
    if (discoFrameRef.current !== null) {
      window.cancelAnimationFrame(discoFrameRef.current);
      discoFrameRef.current = null;
    }

    setIsDiscoActive(false);
    desktopRef.current?.style.setProperty('--disco-pulse', '0');
    desktopRef.current?.style.setProperty('--disco-bass', '0');
    desktopRef.current?.style.setProperty('--disco-spark', '0');
    desktopRef.current?.style.setProperty('--disco-opacity', '0');
    desktopRef.current?.style.setProperty('--disco-scale', '1');
  }

  async function playBackgroundMusic() {
    const audio = backgroundAudioRef.current;
    const gondorAudio = gondorAudioRef.current;
    if (!audio) return;
    if (gondorAudio && !gondorAudio.paused && !gondorAudio.ended) return;

    audio.volume = 0.102;
    try {
      await audio.play();
      setIsBackgroundMusicPlaying(true);
    } catch {
      setIsBackgroundMusicPlaying(false);
      // Autoplay is browser-controlled; a later user gesture will retry playback.
    }
  }

  function toggleBackgroundMusic() {
    const audio = backgroundAudioRef.current;
    if (!audio) return;

    if (!audio.paused && !audio.ended) {
      hasUserPausedBackgroundRef.current = true;
      audio.pause();
      setIsBackgroundMusicPlaying(false);
      return;
    }

    hasUserPausedBackgroundRef.current = false;
    void playBackgroundMusic();
  }

  function finishGondorTheme() {
    stopDiscoLights();
    if (resumeBackgroundAfterGondorRef.current) {
      resumeBackgroundAfterGondorRef.current = false;
      void playBackgroundMusic();
    }
  }

  async function setupGondorAnalyzer(audio: HTMLAudioElement) {
    const audioWindow = window as Window &
      typeof globalThis & { webkitAudioContext?: typeof AudioContext };
    const AudioContextConstructor = audioWindow.AudioContext ?? audioWindow.webkitAudioContext;
    if (!AudioContextConstructor) return;

    const context = audioContextRef.current ?? new AudioContextConstructor();
    audioContextRef.current = context;

    if (!audioAnalyserRef.current) {
      const analyser = context.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.72;
      audioAnalyserRef.current = analyser;
      audioDataRef.current = new Uint8Array(analyser.frequencyBinCount) as Uint8Array<ArrayBuffer>;
    }

    if (!audioSourceRef.current) {
      audioSourceRef.current = context.createMediaElementSource(audio);
      audioSourceRef.current.connect(audioAnalyserRef.current);
      audioAnalyserRef.current.connect(context.destination);
    }

    if (context.state === 'suspended') {
      await context.resume();
    }
  }

  function startDiscoLights() {
    const analyser = audioAnalyserRef.current;
    const data = audioDataRef.current;
    const desktop = desktopRef.current;
    if (!analyser || !data || !desktop) return;

    setIsDiscoActive(true);

    const animate = () => {
      analyser.getByteFrequencyData(data);

      let bassTotal = 0;
      let fullTotal = 0;
      const bassBinCount = Math.min(10, data.length);

      for (let index = 0; index < data.length; index += 1) {
        const value = data[index];
        fullTotal += value;
        if (index < bassBinCount) bassTotal += value;
      }

      const bass = bassTotal / (bassBinCount * 255);
      const full = fullTotal / (data.length * 255);
      const pulse = Math.min(1, bass * 1.65 + full * 0.75);
      const spark = Math.min(1, full * 2.1);
      const opacity = Math.min(0.92, 0.22 + pulse * 0.7);
      const scale = 1 + bass * 0.1;

      desktop.style.setProperty('--disco-pulse', pulse.toFixed(3));
      desktop.style.setProperty('--disco-bass', bass.toFixed(3));
      desktop.style.setProperty('--disco-spark', spark.toFixed(3));
      desktop.style.setProperty('--disco-opacity', opacity.toFixed(3));
      desktop.style.setProperty('--disco-scale', scale.toFixed(3));

      discoFrameRef.current = window.requestAnimationFrame(animate);
    };

    if (discoFrameRef.current !== null) {
      window.cancelAnimationFrame(discoFrameRef.current);
    }
    animate();
  }

  async function playGondorTheme() {
    const audio = gondorAudioRef.current;
    if (!audio) return;

    const backgroundAudio = backgroundAudioRef.current;
    resumeBackgroundAfterGondorRef.current =
      backgroundAudio !== null && !backgroundAudio.paused && !backgroundAudio.ended;
    backgroundAudio?.pause();
    setIsBackgroundMusicPlaying(false);

    audio.currentTime = 0;
    try {
      await setupGondorAnalyzer(audio);
      await audio.play();
      startDiscoLights();
    } catch {
      finishGondorTheme();
      // Browsers may block playback if they no longer consider the click a user gesture.
    }
  }

  async function refreshProjects() {
    try {
      const existingProjects = await api.list_projects();
      setProjects(existingProjects);
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Failed to load previous projects.';
      showMessage(detail, true);
    }
  }

  useEffect(() => {
    void refreshProjects();
  }, []);

  useEffect(() => {
    const startBackgroundMusic = () => {
      if (!hasUserPausedBackgroundRef.current) {
        void playBackgroundMusic();
      }
    };

    void playBackgroundMusic();
    window.addEventListener('pointerdown', startBackgroundMusic);
    window.addEventListener('keydown', startBackgroundMusic);

    return () => {
      window.removeEventListener('pointerdown', startBackgroundMusic);
      window.removeEventListener('keydown', startBackgroundMusic);
    };
  }, []);

  useEffect(
    () => () => {
      if (discoFrameRef.current !== null) {
        window.cancelAnimationFrame(discoFrameRef.current);
      }
    },
    [],
  );

  function openNewProjectModal() {
    setNewProjectName('City Hospital RFP');
    setNewClientName('City Hospital');
    setModalError('');
    setShowNewProjectModal(true);
  }

  function closeNewProjectModal() {
    if (isCreatingProject) return;
    setShowNewProjectModal(false);
    setModalError('');
  }

  async function submitNewProject() {
    const name = newProjectName.trim();
    if (!name) {
      setModalError('Project name is required.');
      return;
    }

    const clientName = newClientName.trim() || null;

    setIsCreatingProject(true);
    setModalError('');
    try {
      const created = await api.create_project({ name, client_name: clientName });
      resetWorkspace();
      setProject(created);
      setProjects((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      setShowNewProjectModal(false);
      showMessage(`Project "${created.name}" created. Upload your RFP to begin.`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Failed to create project.';
      setModalError(detail);
    } finally {
      setIsCreatingProject(false);
    }
  }

  async function selectProject(nextProject: Project) {
    setProject(nextProject);
    setQuestions([]);
    setSelectedQuestion(null);
    setBundle(null);
    setAnswerByQuestion({});
    setFinalText('');

    try {
      const [projectQuestions, documents] = await Promise.all([
        api.list_questions(nextProject.id),
        api.list_documents(nextProject.id),
      ]);

      setQuestions(projectQuestions);
      setSelectedQuestion(projectQuestions[0] ?? null);
      setHasRfpDocument(documents.some((document) => document.document_type === 'rfp'));
      showMessage(`Opened project "${nextProject.name}".`);
    } catch (error) {
      resetWorkspace();
      const detail = error instanceof Error ? error.message : 'Failed to open project.';
      showMessage(detail, true);
    }
  }

  async function handleIntakeRfpUpload(files: FileList | null) {
    const selectedFiles = Array.from(files ?? []);
    if (!selectedFiles.length) return;

    setIsProcessingIntake(true);
    setIntakeResults([]);
    showMessage(`Checking ${selectedFiles.length} RFP file${selectedFiles.length === 1 ? '' : 's'}…`);

    for (const file of selectedFiles) {
      const resultId = `${file.name}-${file.lastModified}-${file.size}`;
      const projectName = file.name.replace(/\.[^.]+$/, '') || 'Uploaded RFP';
      let createdProject: Project | null = null;

      try {
        createdProject = await api.create_project({
          name: projectName,
          client_name: null,
        });
        setProjects((current) => [
          createdProject as Project,
          ...current.filter((item) => item.id !== createdProject?.id),
        ]);

        await api.upload_rfp_document(createdProject.id, file);
        const assessment = await api.assess_rfp(createdProject.id);
        setIntakeResults((current) => [
          ...current,
          {
            id: resultId,
            fileName: file.name,
            project: createdProject,
            assessment,
            error: null,
          },
        ]);
      } catch (error) {
        const detail = error instanceof Error ? error.message : 'Failed to assess RFP.';
        setIntakeResults((current) => [
          ...current,
          {
            id: resultId,
            fileName: file.name,
            project: createdProject,
            assessment: null,
            error: detail,
          },
        ]);
      }
    }

    setIsProcessingIntake(false);
    showMessage('RFP checks completed.');
  }

  function openIntakeFilePicker() {
    intakeRfpInputRef.current?.click();
  }

  async function handleRfpUpload(file: File) {
    if (!project) {
      showMessage('Create a project before uploading an RFP.', true);
      return;
    }

    setIsUploadingRfp(true);
    setHasRfpDocument(false);
    showMessage(`Uploading RFP: ${file.name}`);
    try {
      await api.upload_rfp_document(project.id, file);
      setHasRfpDocument(true);
      showMessage(`RFP uploaded: ${file.name}`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Failed to upload RFP.';
      showMessage(detail, true);
    } finally {
      setIsUploadingRfp(false);
    }
  }

  function openRfpFilePicker() {
    if (!project) {
      showMessage('Create a project before uploading an RFP.', true);
      return;
    }

    rfpInputRef.current?.click();
  }

  async function extractQuestions() {
    if (!project) {
      showMessage('Create a project before extracting requirements.', true);
      return;
    }

    if (isUploadingRfp) {
      showMessage('Wait for the RFP upload to finish before extracting requirements.', true);
      return;
    }

    if (!hasRfpDocument) {
      showMessage('Upload a processed RFP document before extracting requirements.', true);
      return;
    }

    try {
      const extracted = await api.extract_questions(project.id);
      setQuestions(extracted);
      setSelectedQuestion(extracted[0] ?? null);
      setBundle(null);
      setAnswerByQuestion({});
      setFinalText('');
      if (!extracted.length) {
        showMessage('No requirements were found in this RFP. Try another file or check the RFP text.', true);
        return;
      }
      showMessage(`Extracted ${extracted.length} requirements.`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Failed to extract requirements.';
      showMessage(detail, true);
    }
  }

  async function draftAnswer(question: RfpQuestion) {
    const response = await api.draft_answer(question.id);
    setBundle(response);
    setAnswerByQuestion((current) => ({ ...current, [question.id]: response }));
    setFinalText(response.answer.final_text);
    setSelectedQuestion(question);
    setMessage('AI draft generated with source citations.');
  }

  function selectQuestion(question: RfpQuestion) {
    setSelectedQuestion(question);
    const existing = answerByQuestion[question.id];
    if (existing) {
      setBundle(existing);
      setFinalText(existing.answer.final_text);
      return;
    }
    setBundle(null);
    setFinalText('');
  }

  async function saveAnswer() {
    if (!bundle) return;
    const updated = await api.update_answer(bundle.answer.id, { final_text: finalText });
    const nextBundle = { ...bundle, answer: updated as QuestionAnswerBundle['answer'] };
    setBundle(nextBundle);
    setAnswerByQuestion((current) => ({ ...current, [bundle.question_id]: nextBundle }));
    setMessage('Response submitted for review.');
  }

  async function approveAnswer() {
    if (!bundle) return;
    const updated = await api.approve_answer(bundle.answer.id);
    const nextBundle = { ...bundle, answer: updated as QuestionAnswerBundle['answer'] };
    setBundle(nextBundle);
    setAnswerByQuestion((current) => ({ ...current, [bundle.question_id]: nextBundle }));
    setQuestions((current) =>
      current.map((question) =>
        question.id === bundle.question_id ? { ...question, status: 'approved' } : question,
      ),
    );
    setMessage('Response approved.');
  }

  async function exportProject() {
    if (!project) return;
    const result = await api.export_project(project.id);
    const file = await api.download_export_file(result.download_url);
    const objectUrl = URL.createObjectURL(file);
    const downloadLink = document.createElement('a');
    downloadLink.href = objectUrl;
    downloadLink.download = `${project.name.replace(/[^a-z0-9_-]+/gi, '_')}_final_response.pdf`;
    document.body.append(downloadLink);
    downloadLink.click();
    downloadLink.remove();
    URL.revokeObjectURL(objectUrl);
    setMessage(`Exported ${result.exported_answer_count} approved responses to PDF.`);
  }

  return (
    <div ref={desktopRef} className={`desktop ${isDiscoActive ? 'serbian-disco' : ''}`}>
      <audio
        ref={backgroundAudioRef}
        src="/song.mp3"
        preload="auto"
        loop
        onPlay={() => setIsBackgroundMusicPlaying(true)}
        onPause={() => setIsBackgroundMusicPlaying(false)}
      />
      <audio
        ref={gondorAudioRef}
        src={api.sample_data_url('gondor.mp3')}
        preload="auto"
        crossOrigin="anonymous"
        onEnded={finishGondorTheme}
        onPause={() => {
          if (gondorAudioRef.current?.ended) finishGondorTheme();
        }}
      />
      <NewProjectModal
        isOpen={showNewProjectModal}
        isSubmitting={isCreatingProject}
        projectName={newProjectName}
        clientName={newClientName}
        error={modalError}
        onProjectNameChange={setNewProjectName}
        onClientNameChange={setNewClientName}
        onClose={closeNewProjectModal}
        onSubmit={() => void submitNewProject()}
      />

      <aside className="project-sidebar">
        <div className="sidebar-header">
          <div>
            <p className="sidebar-eyebrow">Projects</p>
            <h2>Previous work</h2>
          </div>
          <button
            type="button"
            className="sidebar-new-button"
            disabled={isCreatingProject}
            onClick={openNewProjectModal}
            aria-label="Create new project"
          >
            +
          </button>
        </div>

        <div className="project-list">
          {sortedProjects.length ? (
            sortedProjects.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`project-history-item ${project?.id === item.id ? 'active' : ''}`}
                onClick={() => void selectProject(item)}
              >
                <span className="project-history-name">{item.name}</span>
                <span className="project-history-meta">
                  {item.client_name ?? 'No client'} · {formatProjectDate(item.updated_at)}
                </span>
              </button>
            ))
          ) : (
            <div className="project-history-empty">
              <span>No projects yet</span>
              <small>Create one to start your RFP workspace.</small>
            </div>
          )}
        </div>
      </aside>

      <div className="window">
        <header className="titlebar">
          <div className="title-brand">
            <button
              type="button"
              className="window-title title-music-button"
              onClick={toggleBackgroundMusic}
              aria-pressed={isBackgroundMusicPlaying}
              aria-label={isBackgroundMusicPlaying ? 'Pause background music' : 'Play background music'}
              title={isBackgroundMusicPlaying ? 'Pause background music' : 'Play background music'}
            >
              Serbian Vibe RFP
            </button>
            <button
              type="button"
              className="srb-disco-button"
              onClick={() => void playGondorTheme()}
              aria-label="Play Serbian disco"
              title="Play Serbian disco"
            >
              <img src="/SRB.jpg" alt="" />
            </button>
          </div>
          <div className="titlebar-actions">
            <button
              className="btn-toolbar"
              disabled={isCreatingProject}
              onClick={openNewProjectModal}
            >
              New Project
            </button>
            <button className="btn-toolbar btn-accent" disabled={!project} onClick={exportProject}>
              Export
            </button>
          </div>
        </header>

        <section className="hero-bar">
          <div className="hero-copy">
            <p className="hero-eyebrow">AI-assisted · Human-reviewed</p>
            <h1>{project?.name ?? 'Start a new response'}</h1>
            <p className="hero-sub">
              {project
                ? `${project.client_name ?? 'No client'} — draft trusted answers from the global knowledge base`
                : 'Create a project, upload an RFP, and respond with the shared company knowledge base'}
            </p>
            <div className="hero-intake-actions">
              <button
                type="button"
                className="upload-chip upload-chip-strong"
                disabled={isProcessingIntake}
                onClick={openIntakeFilePicker}
              >
                <span className="upload-icon">↑</span>
                <span>{isProcessingIntake ? 'Checking RFPs…' : 'Check RFPs'}</span>
              </button>
              <input
                ref={intakeRfpInputRef}
                className="file-input-hidden"
                type="file"
                multiple
                accept=".pdf,.docx,.txt,.md"
                onChange={(event) => {
                  void handleIntakeRfpUpload(event.target.files);
                  event.currentTarget.value = '';
                }}
              />
              <span>The machine does the mechanical 80%, the human keeps the 20% that's judgment.</span>
            </div>
          </div>
          <div className="hero-metrics">
            <div className="metric-card">
              <span className="metric-value">{questions.length}</span>
              <span className="metric-label">Requirements</span>
            </div>
            <div className="metric-card">
              <span className="metric-value">{approvedCount}</span>
              <span className="metric-label">Approved</span>
            </div>
            <div className="metric-card metric-progress">
              <span className="metric-value">{progressPct}%</span>
              <span className="metric-label">Complete</span>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progressPct}%` }} />
              </div>
            </div>
          </div>
          {intakeResults.length > 0 && (
            <div className="hero-assessment-results">
              <div className="slider-hint" aria-hidden="true">
                Scroll to see all RFP checks
              </div>
              {intakeResults.map((result) => (
                <article key={result.id} className="hero-assessment-card">
                  <div className="assessment-card-head">
                    <div>
                      <p className="sidebar-eyebrow">{result.fileName}</p>
                      <h2>{result.project?.name ?? 'RFP check failed'}</h2>
                    </div>
                    {result.assessment && (
                      <span className={recommendationClass(result.assessment.recommendation)}>
                        {humanizeStatus(result.assessment.recommendation)}
                      </span>
                    )}
                  </div>

                  {result.error ? (
                    <p className="intake-error">{result.error}</p>
                  ) : (
                    result.assessment && (
                      <>
                        <div className="triage-summary">
                          <div className="assessment-score">
                            <strong>{result.assessment.bid_score}</strong>
                            <span>Bid score</span>
                          </div>
                          <div>
                            <h3>Triage</h3>
                            <p>{result.assessment.summary}</p>
                            {triageFlags(result.assessment).length > 0 && (
                              <div className="red-flag-list">
                                {triageFlags(result.assessment).map((flag) => (
                                  <span key={flag}>{flag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="hero-assessment-grid">
                          <section className="assessment-panel">
                            <h3>Bidder questions</h3>
                            <div className="check-list">
                              {bidderQuestions(result.assessment).length ? (
                                bidderQuestions(result.assessment).map((question, index) => (
                                  <p key={`${question}-${index}`} className="bidder-question">
                                    {question}
                                  </p>
                                ))
                              ) : (
                                <p className="check-empty">No clarification questions detected.</p>
                              )}
                            </div>
                          </section>

                          <section className="assessment-panel">
                            <h3>Compliance matrix</h3>
                            <div className="check-list">
                              {result.assessment.checklist.slice(0, 5).map((item) => (
                                <div key={item.id} className="check-item">
                                  <div>
                                    <strong>{item.label}</strong>
                                    <p>{item.description}</p>
                                  </div>
                                  <span className={severityClass(item.severity)}>
                                    {humanizeStatus(item.status)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </section>
                        </div>

                        <div className="intake-card-actions">
                          <button
                            type="button"
                            className="btn-pill btn-accent"
                            onClick={() => result.project && void selectProject(result.project)}
                          >
                            Open this project
                          </button>
                        </div>
                      </>
                    )
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="toolbar">
          <button type="button" className="upload-chip" onClick={openRfpFilePicker}>
            <span className="upload-icon">↑</span>
            <span>Upload RFP</span>
          </button>
          <input
            ref={rfpInputRef}
            className="file-input-hidden"
            type="file"
            onChange={(event) => {
              if (event.target.files?.[0]) void handleRfpUpload(event.target.files[0]);
              event.currentTarget.value = '';
            }}
          />
          <button
            className="btn-pill btn-accent"
            disabled={!project || !hasRfpDocument || isUploadingRfp}
            onClick={extractQuestions}
          >
            {isUploadingRfp ? 'Uploading RFP…' : 'Extract Requirements'}
          </button>
        </section>

        {message && (
          <div className={`toast ${messageIsError ? 'toast-error' : ''}`} role="status">
            <span className="toast-dot" />
            {message}
          </div>
        )}

        <div className="workspace">
          <section className="requirements-panel">
            <div className="table-header">
              <span>Requirement</span>
              <span>Trust</span>
              <span>Review</span>
            </div>
            <div className="requirement-rows">
              {questions.length > 0 ? (
                questions.map((question, index) => {
                  const rowBundle = answerByQuestion[question.id];
                  const trust = rowBundle ? topTrustScore(rowBundle.citations) : null;
                  const answerStatus = rowBundle?.answer.status;

                  return (
                    <div
                      key={question.id}
                      role="button"
                      tabIndex={0}
                      className={`requirement-row ${selectedQuestion?.id === question.id ? 'selected' : ''}`}
                      onClick={() => selectQuestion(question)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          selectQuestion(question);
                        }
                      }}
                      style={{ animationDelay: `${index * 40}ms` }}
                    >
                      <div>
                        <div className="req-text">{question.question_text}</div>
                        <div className="req-tags">
                          <span className="tag tag-category">{question.category}</span>
                          <span className={statusTagClass(question.status)}>{question.status}</span>
                        </div>
                      </div>
                      <TrustRing score={trust} />
                      <div className="row-actions">
                        <button
                          className="btn-mini"
                          onClick={(event) => {
                            event.stopPropagation();
                            void draftAnswer(question);
                          }}
                        >
                          Draft
                        </button>
                        {answerStatus && (
                          <span className={statusTagClass(answerStatus)}>{answerStatus}</span>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="empty-table">
                  <div className="empty-icon">◇</div>
                  <p>Upload an RFP and extract requirements</p>
                  <span>Your response workspace will appear here</span>
                </div>
              )}
            </div>
          </section>

          <aside className="detail-panel">
            {selectedQuestion ? (
              <>
                <section className="detail-section detail-response">
                  <div className="section-head">
                    <h2>Response</h2>
                    <button className="btn-pill btn-accent" onClick={() => draftAnswer(selectedQuestion)}>
                      Generate
                    </button>
                  </div>
                  <p className="selected-requirement">{selectedQuestion.question_text}</p>
                  {selectedBundle && (
                    <>
                      {selectedBundle.answer.warning && (
                        <p className="warning">{selectedBundle.answer.warning}</p>
                      )}
                      <textarea
                        value={finalText}
                        onChange={(event) => setFinalText(event.target.value)}
                        placeholder="Your AI draft will appear here for review…"
                      />
                      <div className="detail-actions">
                        <button className="btn-pill" onClick={saveAnswer}>
                          Submit
                        </button>
                        <button className="btn-pill btn-accent" onClick={approveAnswer}>
                          Approve
                        </button>
                        <button
                          className="btn-pill btn-danger"
                          onClick={() =>
                            selectedBundle && api.reject_answer(selectedBundle.answer.id)
                          }
                        >
                          Reject
                        </button>
                      </div>
                    </>
                  )}
                </section>

                <section className="detail-section detail-sources">
                  <h2>Sources</h2>
                  <div className="source-list">
                    {selectedBundle?.citations.length ? (
                      selectedBundle.citations.map((citation) => (
                        <article key={citation.id} className="source-card">
                          <div className="source-head">
                            <strong>{citation.document_title}</strong>
                            <span className={trustScoreClass(citation.relevance_score)}>
                              {formatTrustScore(citation.relevance_score)}
                            </span>
                          </div>
                          <p>{citation.excerpt}</p>
                        </article>
                      ))
                    ) : (
                      <div className="empty-detail">
                        <div className="empty-icon">◎</div>
                        <p>Citations appear after generation</p>
                      </div>
                    )}
                  </div>
                </section>
              </>
            ) : (
              <div className="empty-detail empty-detail-large">
                <div className="empty-icon">◈</div>
                <p>Select a requirement</p>
                <span>Review AI responses and trace every source</span>
              </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}
