import React from 'react';

import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'violet' | 'grounded' | 'neutral' | 'warm';
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  className?: string;
  id?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'violet',
  size = 'md',
  icon,
  className,
  id,
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full tracking-wide transition-colors select-none';

  const variants = {
    violet: 'bg-[#EDE7FA] text-[#5B21B6] border border-[#7C3AED]/20',
    grounded: 'bg-[#F0FDF4] text-[#15803D] border border-[#15803D]/25 shadow-grounded',
    neutral: 'bg-white/90 text-[#716B78] border border-[#1E1B24]/10 shadow-sm',
    warm: 'bg-[#F5F2EC] text-[#1E1B24] border border-[#1E1B24]/10',
  };

  const sizes = {
    sm: 'text-xs px-2.5 py-0.5 gap-1 font-medium',
    md: 'text-xs px-3.5 py-1.5 gap-1.5 font-semibold',
  };

  return (
    <span
      id={id}
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
    >
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      {children}
    </span>
  );
};
