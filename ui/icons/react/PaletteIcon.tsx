import React, { memo } from 'react';
import { Icon, IconProps } from './Icon';

export interface PaletteIconProps extends Omit<IconProps, 'name'> {}

/**
 * Palette icon for color/tone analysis
 * Used in: color type tests, tone analysis
 */
export const PaletteIcon = memo<PaletteIconProps>((props) => {
  return <Icon {...props} name="palette" />;
});

PaletteIcon.displayName = 'PaletteIcon';
