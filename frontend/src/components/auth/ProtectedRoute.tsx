import React from 'react';

import { BookOpen, Loader2 } from 'lucide-react';
import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F7FC] flex flex-col items-center justify-center p-6 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-[#7C3AED] text-white flex items-center justify-center shadow-lg shadow-[#7C3AED]/30">
          <BookOpen className="w-6 h-6 animate-pulse" />
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-[#1E1B24] font-sans">DocMind AI</h3>
          <p className="text-xs text-[#716B78] font-mono flex items-center justify-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7C3AED]" />
            Verifying authenticated session...
          </p>
        </div>
      </div>
    );
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};
