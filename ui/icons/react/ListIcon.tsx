import React, { memo } from 'react';
import { Icon, IconProps } from './Icon';

export interface ListIconProps extends Omit<IconProps, 'name'> {}

/**
 * List icon for recommendations and collections
 * Used in: recommendations view, product lists, saved items
 */
export const ListIcon = memo<ListIconProps>((props) => {
  return <Icon {...props} name="list" />;
});

ListIcon.displayName = 'ListIcon';

