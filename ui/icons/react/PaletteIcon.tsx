import React from 'react';

interface PaletteIconProps {
  size?: number;
  className?: string;
}

export const PaletteIcon: React.FC<PaletteIconProps> = ({
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
      <path
        d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10c1.1 0 2-.9 2-2 0-.55-.22-1.05-.59-1.41-.36-.36-.91-.59-1.41-.59H9c-3.31 0-6-2.69-6-6 0-4.97 4.03-9 9-9s9 4.03 9 9c0 2.76-2.24 5-5 5h-1c-.55 0-1 .45-1 1s.45 1 1 1c4.42 0 8-3.58 8-8 0-5.52-4.48-10-10-10z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="7" cy="10" r="1.5" fill="currentColor" opacity="0.3"/>
      <circle cx="12" cy="7" r="1.5" fill="currentColor" opacity="0.5"/>
      <circle cx="17" cy="10" r="1.5" fill="currentColor" opacity="0.7"/>
      <circle cx="10" cy="15" r="1.5" fill="currentColor" opacity="0.9"/>
    </svg>
  );
};