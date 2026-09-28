import React from 'react';

export function PageFrame({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full max-w-[1920px] mx-auto px-6 py-8 md:py-12">
      {children}
    </div>
  );
}
