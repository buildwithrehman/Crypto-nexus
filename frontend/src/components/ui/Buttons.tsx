import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

export function PrimaryButton({ children, className = '', ...props }: ButtonProps) {
  return (
    <button
      className={`border border-structural-border bg-secondary text-neutral px-4 py-2 font-mono uppercase text-xs font-bold tracking-wider transition-none hover:bg-primary hover:text-secondary ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function AccentButton({ children, className = '', ...props }: ButtonProps) {
  return (
    <button
      className={`border border-structural-border bg-primary text-secondary px-4 py-2 font-mono uppercase text-xs font-bold tracking-wider hover:bg-tertiary ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function OutlineButton({ children, className = '', ...props }: ButtonProps) {
  return (
    <button
      className={`border border-structural-border bg-transparent text-secondary px-4 py-2 font-mono uppercase text-xs font-bold tracking-wider hover:bg-surface-accent ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
