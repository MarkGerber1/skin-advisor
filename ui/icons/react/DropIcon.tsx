import React, { memo } from 'react';
import { Icon, IconProps } from './Icon';

export interface DropIconProps extends Omit<IconProps, 'name'> {}

/**
 * Drop/droplet icon for skincare and face diagnostics
 * Used in: skincare tests, face analysis, hydration topics
 */
export const DropIcon = memo<DropIconProps>((props) => {
  return <Icon {...props} name="drop" />;
});

DropIcon.displayName = 'DropIcon';



