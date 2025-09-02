import React, { memo } from 'react';

export interface IconProps {
  name: 'palette' | 'drop' | 'cart' | 'info' | 'list' | 'settings';
  size?: number | string;
  className?: string;
  color?: string;
  'aria-label'?: string;
  'aria-hidden'?: boolean;
}

/**
 * Universal Icon component using SVG sprite
 * Supports all design system icons with proper accessibility
 */
export const Icon = memo<IconProps>(({
  name,
  size = 'var(--icon-size)',
  className = '',
  color = 'currentColor',
  'aria-label': ariaLabel,
  'aria-hidden': ariaHidden = !ariaLabel,
  ...props
}) => {
  return (
    <svg
      width={size}
      height={size}
      className={`icon icon-${name} ${className}`}
      style={{ color }}
      aria-label={ariaLabel}
      aria-hidden={ariaHidden}
      role={ariaLabel ? 'img' : 'presentation'}
      {...props}
    >
      <use href={`#icon-${name}`} />
    </svg>
  );
});

Icon.displayName = 'Icon';

