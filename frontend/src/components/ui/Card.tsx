import React from 'react';

import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'paper' | 'warm' | 'bordered';
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  children,
  className,
  ...props
}) => {
  const baseStyles = 'rounded-2xl transition-all duration-300';

  const variants = {
    default: 'bg-white border border-[#1E1B24]/10 shadow-[0_4px_24px_-4px_rgba(30,27,36,0.05)] hover:shadow-[0_12px_32px_-6px_rgba(30,27,36,0.08)]',
    paper: 'bg-white border border-[#1E1B24]/10 shadow-editorial relative overflow-hidden',
    warm: 'bg-[#F5F2EC] border border-[#1E1B24]/08',
    bordered: 'bg-white/60 backdrop-blur-md border border-[#1E1B24]/10 hover:border-[#7C3AED]/30',
  };

  return (
    <div className={twMerge(clsx(baseStyles, variants[variant], className))} {...props}>
      {children}
    </div>
  );
};
