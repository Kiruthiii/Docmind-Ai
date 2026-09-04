import React, { useState } from 'react';

import { BookOpen, FileText, ArrowRight, ShieldCheck, AlertCircle, Loader2, Eye, EyeOff, KeyRound, CheckCircle2 } from 'lucide-react';
import { Link, useNavigate, Navigate } from 'react-router-dom';

import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { supabase } from '../lib/supabaseClient';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { session, signIn } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Forgot Password flow states
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [resetEmailSent, setResetEmailSent] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);

  // If already authenticated, redirect to /app
  if (session) {
    return <Navigate to="/app" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email || !password) {
      setErrorMessage('Please fill in both email and password.');
      return;
    }

    setLoading(true);

    try {
      const { error } = await signIn(email, password);
      if (error) {
        setErrorMessage(error.message || 'Invalid email or password credentials.');
        setLoading(false);
      } else {
        navigate('/app');
      }
    } catch {
      setErrorMessage('An unexpected network error occurred. Please try again.');
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email) {
      setErrorMessage('Please enter your email address to receive a password reset link.');
      return;
    }

    setResetLoading(true);

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/login`,
      });

      if (error) {
        setErrorMessage(error.message || 'Failed to send password reset email.');
      } else {
        setResetEmailSent(true);
      }
    } catch {
      setErrorMessage('An unexpected network error occurred while sending reset email.');
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F7FC] flex flex-col justify-between selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
      {/* Top Header Bar */}
      <header className="px-4 sm:px-6 py-4 sm:py-6 max-w-7xl mx-auto w-full flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shadow-md group-hover:bg-[#5B21B6] transition-colors">
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
        <Link to="/">
          <Button variant="ghost" size="sm" className="min-h-[44px] text-xs px-2.5 sm:px-3.5">
            <span className="hidden sm:inline">&larr; Back to Landing</span>
            <span className="sm:hidden">&larr; Back</span>
          </Button>
        </Link>
      </header>

      {/* Main Content split view on Desktop */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 flex items-center justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center w-full">
          
          {/* Left Column: Form with Paper Surface Treatment */}
          <div className="lg:col-span-6 max-w-md mx-auto w-full text-left">
            <div className="bg-white p-5 sm:p-8 rounded-2xl sm:rounded-3xl border border-[#1E1B24]/12 shadow-sm space-y-6 relative overflow-hidden">
              {/* Subtle paper background texture effect */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#7C3AED] via-[#5B21B6] to-[#7C3AED]" />

              <div className="space-y-2.5">
                <Badge variant="violet" size="sm" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
                  {isForgotPassword ? 'Account Recovery' : 'Secure Document Sign In'}
                </Badge>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1E1B24] font-sans tracking-tight">
                  {isForgotPassword ? 'Reset password.' : 'Welcome back.'}
                </h1>
                <p className="text-xs sm:text-sm text-[#716B78]">
                  {isForgotPassword
                    ? 'Enter your registered email address to receive a secure recovery link.'
                    : 'Continue to your document workspace and grounded conversations.'}
                </p>
              </div>

              {/* Error Message Box */}
              {errorMessage && (
                <div
                  id="login-error"
                  role="alert"
                  aria-live="polite"
                  className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-3 animate-in fade-in duration-200"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="leading-relaxed">{errorMessage}</div>
                </div>
              )}

              {/* Forgot Password Recovery Sent Banner */}
              {isForgotPassword && resetEmailSent ? (
                <div
                  role="status"
                  aria-live="polite"
                  className="p-6 rounded-2xl bg-[#F0FDF4] border border-[#15803D]/30 space-y-4 animate-in fade-in duration-300"
                >
                  <div className="flex items-center gap-2 text-xs font-sans font-bold text-[#15803D]">
                    <CheckCircle2 className="w-5 h-5 text-[#15803D]" />
                    Password Reset Link Sent
                  </div>
                  <p className="text-xs text-[#1E1B24] leading-relaxed">
                    A password recovery email has been dispatched to <strong>{email}</strong>. Check your inbox and follow the instructions to set a new password.
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="w-full justify-center min-h-[44px]"
                    onClick={() => {
                      setIsForgotPassword(false);
                      setResetEmailSent(false);
                      setErrorMessage(null);
                    }}
                  >
                    Back to Sign In
                  </Button>
                </div>
              ) : isForgotPassword ? (
                /* Forgot Password Form */
                <form onSubmit={handleForgotPassword} className="space-y-5">
                  <div className="space-y-1.5">
                    <label htmlFor="login-email" className="block text-xs font-semibold text-[#1E1B24] font-sans">
                      Email Address
                    </label>
                    <input
                      id="login-email"
                      type="email"
                      required
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      aria-invalid={!!errorMessage}
                      aria-describedby={errorMessage ? "login-error" : undefined}
                      placeholder="name@university.edu"
                      className="w-full min-h-[44px] bg-white border border-[#1E1B24]/15 rounded-xl px-4 py-3 text-sm text-[#1E1B24] placeholder-[#716B78]/60 focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                    />
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    className="w-full justify-center min-h-[44px] font-semibold text-sm"
                    disabled={resetLoading || !email}
                    icon={resetLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
                  >
                    {resetLoading ? 'Sending link...' : 'Send Reset Link'}
                  </Button>

                  <div className="pt-2 text-center">
                    <button
                      type="button"
                      onClick={() => {
                        setIsForgotPassword(false);
                        setErrorMessage(null);
                      }}
                      className="text-xs text-[#7C3AED] font-sans font-semibold hover:underline min-h-[44px] inline-flex items-center justify-center px-2"
                    >
                      &larr; Return to Sign In
                    </button>
                  </div>
                </form>
              ) : (
                /* Standard Login Form */
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-1.5">
                    <label htmlFor="login-email" className="block text-xs font-semibold text-[#1E1B24] font-sans">
                      Email Address
                    </label>
                    <input
                      id="login-email"
                      type="email"
                      required
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      aria-invalid={!!errorMessage}
                      aria-describedby={errorMessage ? "login-error" : undefined}
                      placeholder="name@university.edu"
                      className="w-full min-h-[44px] bg-white border border-[#1E1B24]/15 rounded-xl px-4 py-3 text-sm text-[#1E1B24] placeholder-[#716B78]/60 focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label htmlFor="login-password" className="block text-xs font-semibold text-[#1E1B24] font-sans">
                        Password
                      </label>
                      <button
                        type="button"
                        onClick={() => {
                          setIsForgotPassword(true);
                          setErrorMessage(null);
                        }}
                        className="text-xs text-[#7C3AED] font-sans font-semibold hover:underline inline-flex items-center min-h-[44px] px-1"
                      >
                        Forgot password?
                      </button>
                    </div>
                    <div className="relative">
                      <input
                        id="login-password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        autoComplete="current-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        aria-invalid={!!errorMessage}
                        aria-describedby={errorMessage ? "login-error" : undefined}
                        placeholder="••••••••"
                        className="w-full min-h-[44px] bg-white border border-[#1E1B24]/15 rounded-xl pl-4 pr-12 py-3 text-sm text-[#1E1B24] placeholder-[#716B78]/60 focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-1 top-1/2 -translate-y-1/2 p-2 min-h-[44px] min-w-[44px] flex items-center justify-center text-[#716B78] hover:text-[#1E1B24] transition-colors focus:outline-none focus:ring-2 focus:ring-[#7C3AED] rounded-lg"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    className="w-full justify-center min-h-[44px] py-3.5 font-semibold text-sm"
                    disabled={loading || !email || !password}
                    icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  >
                    {loading ? 'Signing in...' : 'Sign in to Workspace'}
                  </Button>
                </form>
              )}

              <div className="pt-4 border-t border-[#1E1B24]/10 text-xs text-[#716B78] text-center">
                Don&apos;t have an account?{' '}
                <Link to="/signup" className="text-[#7C3AED] font-semibold hover:underline inline-flex items-center min-h-[44px] px-1">
                  Create account
                </Link>
              </div>
            </div>
          </div>

          {/* Right Column: Restrained Editorial Document Visual (Desktop Only) */}
          <div className="hidden lg:block lg:col-span-6 bg-white p-8 rounded-3xl border border-[#1E1B24]/12 shadow-sm space-y-6 text-left">
            <div className="flex items-center justify-between border-b border-[#1E1B24]/08 pb-4">
              <div className="flex items-center gap-2 text-xs font-mono font-semibold text-[#1E1B24]">
                <FileText className="w-4 h-4 text-[#7C3AED]" />
                <span>IEEE_Trans_Transportation_2025.pdf</span>
              </div>
              <Badge variant="grounded" size="sm">
                Evidence Support Checked
              </Badge>
            </div>

            <div className="space-y-3 font-serif italic text-xs text-[#716B78] leading-relaxed">
              <p>
                &ldquo;Section 3.2 — Traffic density (&rho;) is formally defined as: &rho; = N / L, where N represents total vehicle count recorded over segment length L...&rdquo;
              </p>
            </div>

            <div className="pt-4 border-t border-[#1E1B24]/08 flex items-center justify-between text-[11px] font-mono text-[#7C3AED] font-semibold">
              <span>[Cited: Page 14, ¶3]</span>
              <span>DocMind Session Ready</span>
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-xs text-[#716B78] font-mono border-t border-[#1E1B24]/08">
        DocMind AI &bull; Evidence-Grounded PDF Intelligence
      </footer>
    </div>
  );
};
