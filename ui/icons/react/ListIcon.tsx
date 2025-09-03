import React from 'react';

interface ListIconProps {
  size?: number;
  className?: string;
}

/**
 * 📋 List icon for recommendations
 * Uses design system tokens: --icon-size: 24px
 * Supports touch targets: min-width/height via size prop
 */
export const ListIcon: React.FC<ListIconProps> = ({
  size = 24,
  className = ''
}) => {
  const iconSize = Math.max(size, 24); // Minimum touch target

  return (
    <svg
      width={iconSize}
      height={iconSize}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      style={{
        display: 'inline-block',
        verticalAlign: 'middle',
        minWidth: 'var(--touch-size, 48px)',
        minHeight: 'var(--touch-size, 48px)'
      }}
      role="img"
      aria-label="Recommendations list"
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