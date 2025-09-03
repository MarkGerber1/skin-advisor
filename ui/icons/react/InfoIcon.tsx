import React from 'react';

interface InfoIconProps {
  size?: number;
  className?: string;
}

/**
 * ℹ️ Info icon for information
 * Uses design system tokens: --icon-size: 24px
 * Supports touch targets: min-width/height via size prop
 */
export const InfoIcon: React.FC<InfoIconProps> = ({
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
      aria-label="Information"
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 16V12" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="12" cy="8" r="1" fill="currentColor"/>
    </svg>
  );
};