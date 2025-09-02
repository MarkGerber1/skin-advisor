import React, { memo } from 'react';
import { Icon, IconProps } from './Icon';

export interface InfoIconProps extends Omit<IconProps, 'name'> {}

/**
 * Information/help icon
 * Used in: help sections, bot info, tooltips
 */
export const InfoIcon = memo<InfoIconProps>((props) => {
  return <Icon {...props} name="info" />;
});

InfoIcon.displayName = 'InfoIcon';
