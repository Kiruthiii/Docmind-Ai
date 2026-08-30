import React, { useState, useRef, useEffect } from 'react';
import { BookOpen, ChevronDown, LogOut, Menu, X, FolderCheck } from 'lucide-react';
import type { User } from '@supabase/supabase-js';

interface AppHeaderProps {
  user: User | null;
  activeWorkspaceName?: string;
  onSignOut: () => Promise<void>;
  isMobileDrawerOpen: boolean;
  onToggleMobileDrawer: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  user,
  activeWorkspaceName,
  onSignOut,
  isMobileDrawerOpen,
  onToggleMobileDrawer,
}) => {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Extract display name & initials
  const fullName = user?.user_metadata?.full_name;
  const email = user?.email || '';
  const displayName = fullName || email.split('@')[0] || 'Researcher';
  const initial = (fullName ? fullName[0] : email ? email[0] : 'U').toUpperCase();

  // Close dropdown on Escape key or outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setUserMenuOpen(false);
      }
    };

    if (userMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [userMenuOpen]);

  return (
    <header className="bg-white border-b border-[#1E1B24]/10 sticky top-0 z-40 selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-18">
          
          {/* Left Branding & Mobile Hamburger */}
          <div className="flex items-center gap-3">
            <button
              onClick={onToggleMobileDrawer}
              className="lg:hidden p-2 rounded-xl text-[#1E1B24] hover:bg-[#F8F7FC] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label={isMobileDrawerOpen ? "Close sidebar menu" : "Open sidebar menu"}
              aria-expanded={isMobileDrawerOpen}
              aria-controls="mobile-sidebar-drawer"
              type="button"
            >
              {isMobileDrawerOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            <div className="flex items-center gap-2.5 select-none">
              <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shadow-sm shadow-[#7C3AED]/20">
                <BookOpen className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>
              <div className="flex flex-col text-left">
                <span className="text-base sm:text-lg font-bold tracking-tight text-[#1E1B24] font-sans flex items-center gap-1 leading-none">
                  DocMind <span className="text-[#7C3AED]">AI</span>
                </span>
                <span className="text-[9px] tracking-wider text-[#716B78] uppercase font-mono mt-0.5 hidden sm:inline-block">
                  Document Intelligence
                </span>
              </div>
            </div>
          </div>

          {/* Center Active Workspace Indicator */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#F8F7FC] border border-[#1E1B24]/08 text-xs text-[#1E1B24]">
            <FolderCheck className="w-3.5 h-3.5 text-[#7C3AED]" />
            <span className="font-mono text-[#716B78] text-[11px]">Workspace:</span>
            <span className="font-semibold max-w-[200px] truncate text-[#1E1B24]">
              {activeWorkspaceName || 'No Active Workspace'}
            </span>
          </div>

          {/* Right User Dropdown & Actions */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setUserMenuOpen((prev) => !prev)}
              aria-expanded={userMenuOpen}
              aria-haspopup="true"
              aria-label="User profile menu"
              className="flex items-center gap-2.5 p-1.5 sm:px-3 sm:py-1.5 rounded-xl hover:bg-[#F8F7FC] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] transition-colors border border-transparent hover:border-[#1E1B24]/08 min-h-[44px]"
            >
              <div className="w-8 h-8 rounded-full bg-[#EDE7FA] border border-[#7C3AED]/20 text-[#5B21B6] font-bold text-xs flex items-center justify-center shrink-0">
                {initial}
              </div>
              
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-semibold text-[#1E1B24] max-w-[120px] lg:max-w-[180px] truncate leading-snug">
                  {displayName}
                </span>
                <span className="text-[10px] text-[#716B78] font-mono max-w-[120px] lg:max-w-[180px] truncate">
                  {email}
                </span>
              </div>

              <ChevronDown className={`w-4 h-4 text-[#716B78] transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            {userMenuOpen && (
              <div
                role="menu"
                aria-orientation="vertical"
                className="absolute right-0 mt-2 w-64 bg-white rounded-2xl border border-[#1E1B24]/12 shadow-lg shadow-[#1E1B24]/05 py-2 z-50 animate-in fade-in-50 zoom-in-95 duration-150 text-left"
              >
                <div className="px-4 py-3 border-b border-[#1E1B24]/08 space-y-0.5">
                  <p className="text-xs font-bold text-[#1E1B24] truncate">{displayName}</p>
                  <p className="text-[11px] text-[#716B78] font-mono truncate">{email}</p>
                  <div className="pt-1.5 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#15803D]" />
                    <span className="text-[10px] text-[#15803D] font-medium font-mono uppercase tracking-wider">
                      Authenticated Session
                    </span>
                  </div>
                </div>

                <div className="p-1.5">
                  <button
                    type="button"
                    role="menuitem"
                    onClick={async () => {
                      setUserMenuOpen(false);
                      await onSignOut();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-600 hover:bg-red-50 rounded-xl transition-colors font-medium min-h-[44px] focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
                  >
                    <LogOut className="w-4 h-4 shrink-0" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </header>
  );
};
