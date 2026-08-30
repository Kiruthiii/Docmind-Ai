import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, ArrowRight, BookOpen } from 'lucide-react';
import { Button } from '../ui/Button';

export const Header: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-[#1E1B24]/08 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shadow-md shadow-[#7C3AED]/25 group-hover:bg-[#5B21B6] transition-colors">
              <BookOpen className="w-5 h-5" />
            </div>
            <div className="flex flex-col text-left">
              <span className="text-xl font-bold tracking-tight text-[#1E1B24] font-sans flex items-center gap-1">
                DocMind <span className="text-[#7C3AED]">AI</span>
              </span>
              <span className="text-[10px] tracking-widest text-[#716B78] uppercase font-semibold">
                Document Intelligence
              </span>
            </div>
          </Link>

          {/* Desktop Nav Items */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[#716B78]">
            <a href="#document-stage" className="hover:text-[#7C3AED] focus-visible:text-[#7C3AED] focus-visible:outline-none transition-colors">
              Story Stage
            </a>
            <a href="#problem" className="hover:text-[#7C3AED] focus-visible:text-[#7C3AED] focus-visible:outline-none transition-colors">
              The Problem
            </a>
            <a href="#how-it-works" className="hover:text-[#7C3AED] focus-visible:text-[#7C3AED] focus-visible:outline-none transition-colors">
              How It Works
            </a>
            <a href="#use-cases" className="hover:text-[#7C3AED] focus-visible:text-[#7C3AED] focus-visible:outline-none transition-colors">
              Use Cases
            </a>
            <a href="#product-reveal" className="hover:text-[#7C3AED] focus-visible:text-[#7C3AED] focus-visible:outline-none transition-colors">
              Workspace Preview
            </a>
          </nav>

          {/* Action CTAs linked to Auth Routes */}
          <div className="hidden md:flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/signup">
              <Button variant="primary" size="sm" icon={<ArrowRight className="w-4 h-4" />}>
                Get Started Free
              </Button>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-[#1E1B24] hover:bg-[#EDE7FA] focus-visible:ring-2 focus-visible:ring-[#7C3AED] focus-visible:outline-none transition-colors"
              aria-label="Toggle Navigation Menu"
              aria-expanded={mobileMenuOpen}
              id="mobile-menu-toggle-btn"
              type="button"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-[#1E1B24]/10 px-4 pt-3 pb-6 space-y-4 shadow-lg animate-in slide-in-from-top duration-200">
          <nav className="flex flex-col space-y-3 text-sm font-medium text-[#1E1B24]">
            <a
              href="#document-stage"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-[#F8F7FC] transition-colors"
            >
              Story Stage
            </a>
            <a
              href="#problem"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-[#F8F7FC] transition-colors"
            >
              The Problem
            </a>
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-[#F8F7FC] transition-colors"
            >
              How It Works
            </a>
            <a
              href="#use-cases"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-[#F8F7FC] transition-colors"
            >
              Use Cases
            </a>
            <a
              href="#product-reveal"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-[#F8F7FC] transition-colors"
            >
              Workspace Preview
            </a>
          </nav>
          <div className="pt-2 border-t border-[#1E1B24]/10 flex flex-col gap-2">
            <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="outline" size="md" className="w-full">
                Sign In
              </Button>
            </Link>
            <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="primary" size="md" className="w-full" icon={<ArrowRight className="w-4 h-4" />}>
                Get Started Free
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
