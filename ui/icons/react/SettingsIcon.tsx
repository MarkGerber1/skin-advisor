import React, { memo } from 'react';
import { Icon, IconProps } from './Icon';

export interface SettingsIconProps extends Omit<IconProps, 'name'> {}

/**
 * Settings/gear icon
 * Used in: settings menu, configuration, preferences
 */
export const SettingsIcon = memo<SettingsIconProps>((props) => {
  return <Icon {...props} name="settings" />;
});

SettingsIcon.displayName = 'SettingsIcon';



