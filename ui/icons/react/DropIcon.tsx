import React from 'react';

interface DropIconProps {
  size?: number;
  className?: string;
}

/**
 * 💧 Drop icon for skincare/face diagnosis
 * Uses design system tokens: --icon-size: 24px
 * Supports touch targets: min-width/height via size prop
 */
export const DropIcon: React.FC<DropIconProps> = ({
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
      aria-label="Skincare drop"
    >
      <path
        d="M12 2.5c0 0-5 4.5-5 9.5a5 5 0 0 0 10 0c0-5-5-9.5-5-9.5z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d="M9.5 10.5c0-1.5 1-3 2.5-4"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.4"
      />
    </svg>
  );
};