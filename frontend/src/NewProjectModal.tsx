import { useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';

type NewProjectModalProps = {
  isOpen: boolean;
  isSubmitting: boolean;
  projectName: string;
  clientName: string;
  error: string;
  onProjectNameChange: (value: string) => void;
  onClientNameChange: (value: string) => void;
  onClose: () => void;
  onSubmit: () => void;
};

export function NewProjectModal({
  isOpen,
  isSubmitting,
  projectName,
  clientName,
  error,
  onProjectNameChange,
  onClientNameChange,
  onClose,
  onSubmit,
}: NewProjectModalProps) {
  const titleId = useId();
  const projectNameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    projectNameRef.current?.focus();
    projectNameRef.current?.select();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div
      className="modal-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isSubmitting) {
          onClose();
        }
      }}
    >
      <div
        className="modal-window"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-titlebar">
          <div className="traffic-lights">
            <button
              type="button"
              className="light red"
              aria-label="Close"
              disabled={isSubmitting}
              onClick={onClose}
            />
            <span className="light yellow" aria-hidden="true" />
            <span className="light green" aria-hidden="true" />
          </div>
          <span className="window-title">New Project</span>
          <button
            type="button"
            className="modal-close"
            aria-label="Close"
            disabled={isSubmitting}
            onClick={onClose}
          >
            ×
          </button>
        </header>

        <div className="modal-body">
          <h2 id={titleId}>Create a new RFP response</h2>
          <p>Set up a workspace for one tender. You can upload documents after creating the project.</p>
          {error && <p className="modal-error">{error}</p>}

          <div className="modal-field">
            <label htmlFor="project-name">Project name</label>
            <input
              ref={projectNameRef}
              id="project-name"
              type="text"
              value={projectName}
              onChange={(event) => onProjectNameChange(event.target.value)}
              placeholder="e.g. City Hospital RFP"
              autoComplete="off"
              disabled={isSubmitting}
            />
          </div>

          <div className="modal-field">
            <label htmlFor="client-name">Client name</label>
            <input
              id="client-name"
              type="text"
              value={clientName}
              onChange={(event) => onClientNameChange(event.target.value)}
              placeholder="e.g. City Hospital"
              autoComplete="off"
              disabled={isSubmitting}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault();
                  onSubmit();
                }
              }}
            />
          </div>
        </div>

        <footer className="modal-footer">
          <button
            type="button"
            className="btn-pill btn-muted"
            disabled={isSubmitting}
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn-pill btn-accent"
            disabled={isSubmitting}
            onClick={onSubmit}
          >
            {isSubmitting ? 'Creating…' : 'Create Project'}
          </button>
        </footer>
      </div>
    </div>,
    document.body,
  );
}
