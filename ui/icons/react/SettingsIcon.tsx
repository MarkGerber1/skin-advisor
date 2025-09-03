import React from 'react';

interface SettingsIconProps {
  size?: number;
  className?: string;
}

/**
 * ⚙️ Settings icon for configuration
 * Uses design system tokens: --icon-size: 24px
 * Supports touch targets: min-width/height via size prop
 */
export const SettingsIcon: React.FC<SettingsIconProps> = ({
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
      aria-label="Settings"
    >
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 1V3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 21V23" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M4.22 4.22L5.64 5.64" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M18.36 18.36L19.78 19.78" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M1 12H3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M21 12H23" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M4.22 19.78L5.64 18.36" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M18.36 5.64L19.78 4.22" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
};