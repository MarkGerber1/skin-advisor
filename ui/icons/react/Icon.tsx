import React from 'react';

interface IconProps {
  name: 'palette' | 'drop' | 'cart' | 'info' | 'list' | 'settings';
  size?: number;
  className?: string;
}

export const Icon: React.FC<IconProps> = ({
  name,
  size = 24,
  className = ''
}) => {
  return (
    <svg
      width={size}
      height={size}
      className={className}
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
    >
      <use href={`#icon-${name}`} />
    </svg>
  );
};