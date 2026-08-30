import React, { useState, useEffect, useRef } from 'react';
import { X, FolderPlus, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';

interface CreateWorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string) => Promise<void>;
  isCreating: boolean;
  error: string | null;
}

export const CreateWorkspaceModal: React.FC<CreateWorkspaceModalProps> = ({
  isOpen,
  onClose,
  onCreate,
  isCreating,
  error,
}) => {
  const [name, setName] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset name & focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setName('');
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  // Handle Keyboard Escape key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isCreating) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isCreating, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || isCreating) return;
    await onCreate(name.trim());
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#1E1B24]/40 backdrop-blur-xs transition-opacity"
        onClick={() => {
          if (!isCreating) onClose();
        }}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-workspace-title"
        className="relative w-full max-w-md bg-white rounded-2xl border border-[#1E1B24]/12 shadow-2xl p-6 sm:p-7 text-left space-y-6 animate-in fade-in-50 zoom-in-95 duration-150"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center shrink-0">
              <FolderPlus className="w-5 h-5" />
            </div>
            <div>
              <h2 id="create-workspace-title" className="text-base sm:text-lg font-bold text-[#1E1B24] font-sans">
                Create Research Workspace
              </h2>
              <p className="text-xs text-[#716B78]">
                Group relevant documents and queries under a unique workspace.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isCreating}
            aria-label="Close modal"
            className="p-2 rounded-xl text-[#716B78] hover:text-[#1E1B24] hover:bg-[#F8F7FC] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] min-h-[44px] min-w-[44px] flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* API Error Notification inside Modal */}
        {error && (
          <div
            role="alert"
            aria-live="polite"
            className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2.5"
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label htmlFor="workspace-name-input" className="block text-xs font-semibold text-[#1E1B24]">
              Workspace Name <span className="text-red-500">*</span>
            </label>
            <input
              id="workspace-name-input"
              ref={inputRef}
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Legal Analysis Q3 or AI Research Papers"
              disabled={isCreating}
              className="w-full min-h-[44px] bg-[#F8F7FC] border border-[#1E1B24]/15 rounded-xl px-4 py-2.5 text-xs text-[#1E1B24] placeholder-[#716B78] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#7C3AED] transition-all"
            />
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={onClose}
              disabled={isCreating}
              className="min-h-[44px]"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={isCreating || !name.trim()}
              icon={isCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
              className="min-h-[44px]"
            >
              {isCreating ? 'Creating Workspace...' : 'Create Workspace'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
