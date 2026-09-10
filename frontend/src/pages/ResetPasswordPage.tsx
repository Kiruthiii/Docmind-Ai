import React, { useState, useEffect } from 'react';
import { BookOpen, KeyRound, Eye, EyeOff, Loader2, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabaseClient';

export const ResetPasswordPage: React.FC = () => {
  const { updatePassword, setIsPasswordRecovery } = useAuth();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    // If URL hash contains recovery token, mark password recovery mode active
    if (window.location.hash.includes('type=recovery') || window.location.search.includes('type=recovery')) {
      setIsPasswordRecovery(true);
    }
  }, [setIsPasswordRecovery]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!newPassword || !confirmPassword) {
      setErrorMessage('Please fill in both password fields.');
      return;
    }

    if (newPassword.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please verify both fields.');
      return;
    }

    setLoading(true);

    try {
      const { error } = await updatePassword(newPassword);
      if (error) {
        setErrorMessage(error.message || 'Failed to reset password. The link may have expired.');
      } else {
        setIsSuccess(true);
      }
    } catch {
      setErrorMessage('An unexpected error occurred while updating your password.');
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = async () => {
    await supabase.auth.signOut();
    setIsPasswordRecovery(false);
    navigate('/login');
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
      </header>

      {/* Main Card Container */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-md bg-white border border-[#E9E4F0] rounded-2xl shadow-xl p-8 text-left transition-all">
          {isSuccess ? (
            <div className="text-center py-4 space-y-6">
              <div className="w-16 h-16 rounded-full bg-[#ECFDF5] text-[#059669] flex items-center justify-center mx-auto shadow-inner">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-[#1E1B24]">Password Reset Successful!</h2>
                <p className="text-sm text-[#716B78]">
                  Your password has been updated securely. You can now log in using your new password.
                </p>
              </div>
              <Button
                onClick={handleFinish}
                className="w-full py-3 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-medium rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
              >
                Log In With New Password <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="mb-6 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="violet" className="flex items-center gap-1.5 px-3 py-1">
                    <KeyRound className="w-3.5 h-3.5 text-[#7C3AED]" /> Security Recovery
                  </Badge>
                </div>
                <h1 className="text-2xl font-bold text-[#1E1B24]">Set New Password</h1>
                <p className="text-sm text-[#716B78]">
                  Please enter your new account password below.
                </p>
              </div>

              {/* Error Message */}
              {errorMessage && (
                <div className="mb-6 p-4 rounded-xl bg-[#FEF2F2] border border-[#FCA5A5] text-[#991B1B] text-sm flex items-start gap-3 shadow-sm animate-in fade-in duration-200">
                  <AlertCircle className="w-5 h-5 text-[#DC2626] shrink-0 mt-0.5" />
                  <div className="flex-1 font-medium">{errorMessage}</div>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-[#4A4453] uppercase tracking-wider mb-2">
                    New Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••••••"
                      required
                      className="w-full px-4 py-3 pr-10 border border-[#DDD6FE] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all bg-[#FAF8FF] text-[#1E1B24]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#4B5563] transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#4A4453] uppercase tracking-wider mb-2">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••••••"
                      required
                      className="w-full px-4 py-3 pr-10 border border-[#DDD6FE] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all bg-[#FAF8FF] text-[#1E1B24]"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-semibold rounded-xl shadow-md transition-all flex items-center justify-center gap-2 mt-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Updating Password...
                    </>
                  ) : (
                    <>
                      Update Password <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              </form>
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 text-center text-xs text-[#9CA3AF]">
        DocMind AI Intelligence Platform &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
};

export default ResetPasswordPage;
