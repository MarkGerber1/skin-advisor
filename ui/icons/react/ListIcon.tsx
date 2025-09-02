import React from 'react';

interface ListIconProps {
  size?: number;
  className?: string;
}

export const ListIcon: React.FC<ListIconProps> = ({
  size = 24,
  className = ''
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
    >
      <line x1="8" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="8" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="8" y1="18" x2="21" y2="18" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="3" y1="6" x2="3.01" y2="6" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="3" y1="12" x2="3.01" y2="12" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="3" y1="18" x2="3.01" y2="18" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
};