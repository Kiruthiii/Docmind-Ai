import React, { useState } from 'react';

import { BookOpen, FileText, ArrowRight, ShieldCheck, AlertCircle, Loader2, CheckCircle2, Eye, EyeOff, XCircle } from 'lucide-react';
import { Link, useNavigate, Navigate } from 'react-router-dom';

import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';

export const SignupPage: React.FC = () => {
  const { session, signUp } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [confirmationSent, setConfirmationSent] = useState(false);

  // If already authenticated, redirect to /app
  if (session) {
    return <Navigate to="/app" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setConfirmationSent(false);

    if (!email || !password) {
      setErrorMessage('Please enter your email and password.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please check and try again.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);

    try {
      const { error, user, session: newSession } = await signUp(email, password, fullName);
      if (error) {
        setErrorMessage(error.message || 'Signup failed. Please try again.');
        setLoading(false);
      } else if (newSession) {
        // Auto-confirmed login, navigate to app
        navigate('/app');
      } else if (user) {
        // Email confirmation required by Supabase auth
        setConfirmationSent(true);
        setLoading(false);
      } else {
        setConfirmationSent(true);
        setLoading(false);
      }
    } catch {
      setErrorMessage('An unexpected network error occurred. Please try again.');
      setLoading(false);
    }
  };

  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;
  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword;

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
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8 flex items-center justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center w-full">
          
          {/* Left Column: Form with Paper Surface Treatment */}
          <div className="lg:col-span-6 max-w-md mx-auto w-full text-left">
            <div className="bg-white p-5 sm:p-8 rounded-2xl sm:rounded-3xl border border-[#1E1B24]/12 shadow-sm space-y-5 relative overflow-hidden">
              {/* Subtle paper background texture accent */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#7C3AED] via-[#5B21B6] to-[#7C3AED]" />

              <div className="space-y-2">
                <Badge variant="violet" size="sm" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
                  Create Account
                </Badge>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1E1B24] font-sans tracking-tight">
                  Create your account.
                </h1>
                <p className="text-xs sm:text-sm text-[#716B78]">
                  Start working with your documents and evidence-grounded Q&amp;A.
                </p>
              </div>

              {/* Error Message Box */}
              {errorMessage && (
                <div
                  id="signup-error"
                  role="alert"
                  aria-live="polite"
                  className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-3 animate-in fade-in duration-200"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="leading-relaxed">{errorMessage}</div>
                </div>
              )}

              {/* Confirmation Sent Notice */}
              {confirmationSent ? (
                <div
                  role="status"
                  aria-live="polite"
                  className="p-6 rounded-2xl bg-[#F0FDF4] border border-[#15803D]/30 space-y-4 animate-in fade-in duration-300"
                >
                  <div className="flex items-center gap-2 text-xs font-sans font-bold text-[#15803D]">
                    <CheckCircle2 className="w-5 h-5 text-[#15803D]" />
                    Account Registration Successful
                  </div>
                  <p className="text-xs text-[#1E1B24] leading-relaxed">
                    A confirmation email has been sent to <strong>{email}</strong>. Please check your inbox and verify your email address to sign in.
                  </p>
                  <div className="pt-2">
                    <Link to="/login">
                      <Button variant="primary" size="sm" className="w-full justify-center min-h-[44px]">
                        Proceed to Sign In
                      </Button>
                    </Link>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <label htmlFor="signup-fullname" className="block text-xs font-semibold text-[#1E1B24] font-sans">
                      Full Name
                    </label>
                    <input
                      id="signup-fullname"
                      type="text"
                      autoComplete="name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Dr. Alexander Vance"
                      className="w-full min-h-[44px] bg-white border border-[#1E1B24]/15 rounded-xl px-4 py-3 text-sm text-[#1E1B24] placeholder-[#716B78]/60 focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label htmlFor="signup-email" className="block text-xs font-semibold text-[#1E1B24] font-sans">
                      Email Address
                    </label>
                    <input
                      id="signup-email"
                      type="email"
                      required
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      aria-invalid={!!errorMessage}
                      aria-describedby={errorMessage ? "signup-error" : undefined}
                      placeholder="name@university.edu"
                      className="w-full min-h-[44px] bg-white border border-[#1E1B24]/15 rounded-xl px-4 py-3 text-sm text-[#1E1B24] placeholder-[#716B78]/60 focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label htmlFor="signup-password" className="block text-xs font-semibold text-[#1E1B24] font-sans">
                      Password
                    </label>
                    <div className="relative">
                      <input
                        id="signup-password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        autoComplete="new-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        aria-invalid={!!errorMessage || (password.length > 0 && password.length < 6)}
                        aria-describedby={errorMessage ? "signup-error" : undefined}
                        placeholder="At least 6 characters"
                        className="w-full min-h-[44px] bg-white border border-[#1E1B24]/15 rounded-xl pl-4 pr-12 py-3 text-sm text-[#1E1B24] placeholder-[#716B78]/60 focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-1 top-1/2 -translate-y-1/2 p-2 min-h-[44px] min-w-[44px] flex items-center justify-center text-[#716B78] hover:text-[#1E1B24] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] rounded-lg"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {password.length > 0 && password.length < 6 && (
                      <p className="text-[11px] text-amber-600 font-sans font-medium flex items-center gap-1 mt-1">
                        <AlertCircle className="w-3 h-3" /> Password must be at least 6 characters long
                      </p>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <label htmlFor="signup-confirm-password" className="block text-xs font-semibold text-[#1E1B24] font-sans">
                      Confirm Password
                    </label>
                    <div className="relative">
                      <input
                        id="signup-confirm-password"
                        type={showConfirmPassword ? 'text' : 'password'}
                        required
                        autoComplete="new-password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        aria-invalid={passwordsMismatch || !!errorMessage}
                        aria-describedby={
                          errorMessage
                            ? "signup-error"
                            : (passwordsMatch || passwordsMismatch)
                            ? "password-match-status"
                            : undefined
                        }
                        placeholder="Re-enter password"
                        className={`w-full min-h-[44px] bg-white border rounded-xl pl-4 pr-12 py-3 text-sm text-[#1E1B24] placeholder-[#716B78]/60 focus:outline-none focus:ring-2 transition-all ${
                          passwordsMatch
                            ? 'border-emerald-500 focus:ring-emerald-500'
                            : passwordsMismatch
                            ? 'border-red-500 focus:ring-red-500'
                            : 'border-[#1E1B24]/15 focus:ring-[#7C3AED]'
                        }`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-1 top-1/2 -translate-y-1/2 p-2 min-h-[44px] min-w-[44px] flex items-center justify-center text-[#716B78] hover:text-[#1E1B24] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] rounded-lg"
                        aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                      >
                        {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>

                    {/* Real-time Password Match Feedback Indicator */}
                    <div id="password-match-status" role="status" aria-live="polite">
                      {passwordsMatch && (
                        <p className="text-[11px] text-emerald-600 font-sans font-medium flex items-center gap-1 mt-1 animate-in fade-in duration-150">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Passwords match
                        </p>
                      )}
                      {passwordsMismatch && (
                        <p className="text-[11px] text-red-600 font-sans font-medium flex items-center gap-1 mt-1 animate-in fade-in duration-150">
                          <XCircle className="w-3.5 h-3.5 text-red-600" /> Passwords do not match
                        </p>
                      )}
                    </div>
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    className="w-full justify-center min-h-[44px] py-3.5 font-semibold text-sm mt-2"
                    disabled={loading || !email || !password || !confirmPassword || passwordsMismatch}
                    icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  >
                    {loading ? 'Creating account...' : 'Create Account'}
                  </Button>
                </form>
              )}

              <div className="pt-4 border-t border-[#1E1B24]/10 text-xs text-[#716B78] text-center">
                Already have an account?{' '}
                <Link to="/login" className="text-[#7C3AED] font-semibold hover:underline inline-flex items-center min-h-[44px] px-1">
                  Sign in
                </Link>
              </div>
            </div>
          </div>

          {/* Right Column: Restrained Editorial Document Visual (Desktop Only) */}
          <div className="hidden lg:block lg:col-span-6 bg-white p-8 rounded-3xl border border-[#1E1B24]/12 shadow-sm space-y-6 text-left">
            <div className="flex items-center justify-between border-b border-[#1E1B24]/08 pb-4">
              <div className="flex items-center gap-2 text-xs font-mono font-semibold text-[#1E1B24]">
                <FileText className="w-4 h-4 text-[#7C3AED]" />
                <span>DocMind Workspace Account</span>
              </div>
              <Badge variant="grounded" size="sm">
                Evidence Pipeline
              </Badge>
            </div>

            <div className="space-y-3 font-serif italic text-xs text-[#716B78] leading-relaxed">
              <p>
                &ldquo;DocMind AI checks whether retrieved evidence supports the question before generating. Answers are anchored to verifiable page-level citations.&rdquo;
              </p>
            </div>

            <div className="pt-4 border-t border-[#1E1B24]/08 flex items-center justify-between text-[11px] font-mono text-[#7C3AED] font-semibold">
              <span>Ready for academic &amp; technical PDFs</span>
              <span>Fast &amp; Secure</span>
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
