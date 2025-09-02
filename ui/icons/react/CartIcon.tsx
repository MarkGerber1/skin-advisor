import React, { memo } from 'react';
import { Icon, IconProps } from './Icon';

export interface CartIconProps extends Omit<IconProps, 'name'> {}

/**
 * Shopping cart icon
 * Used in: cart navigation, product purchase flows
 */
export const CartIcon = memo<CartIconProps>((props) => {
  return <Icon {...props} name="cart" />;
});

CartIcon.displayName = 'CartIcon';



