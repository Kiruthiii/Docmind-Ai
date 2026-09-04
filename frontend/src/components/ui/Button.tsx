import React from 'react';

import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  icon,
  iconPosition = 'right',
  className,
  type = 'button',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-300 ease-out focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl cursor-pointer select-none';

  const variants = {
    primary: 'bg-[#7C3AED] hover:bg-[#5B21B6] text-white shadow-md hover:shadow-lg shadow-[#7C3AED]/20 active:scale-[0.98]',
    secondary: 'bg-[#EDE7FA] hover:bg-[#D8D3E6] text-[#5B21B6] border border-[#7C3AED]/10 active:scale-[0.98]',
    outline: 'bg-white/90 hover:bg-[#F8F7FC] text-[#1E1B24] border border-[#1E1B24]/15 shadow-sm active:scale-[0.98]',
    ghost: 'text-[#1E1B24] hover:bg-[#EDE7FA]/60 hover:text-[#5B21B6]',
  };

  const sizes = {
    sm: 'text-xs px-3.5 py-2 min-h-[36px] gap-1.5',
    md: 'text-sm px-5 py-2.5 min-h-[44px] gap-2 font-medium',
    lg: 'text-base px-7 py-3.5 min-h-[48px] gap-2.5 font-semibold',
  };

  return (
    <button
      type={type}
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      {...props}
    >
      {icon && iconPosition === 'left' && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{children}</span>
      {icon && iconPosition === 'right' && <span className="inline-flex shrink-0">{icon}</span>}
    </button>
  );
};
