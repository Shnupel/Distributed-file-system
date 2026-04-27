import type { ButtonHTMLAttributes, ReactNode } from "react";

import styles from "./Button.module.scss";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "outline" | "ghost";
  size?: "sm" | "md";
  icon?: ReactNode;
};

export const Button = ({
  variant = "primary",
  size = "md",
  icon,
  className,
  children,
  ...props
}: ButtonProps) => {
  const classes = [styles.button, styles[variant], styles[size], className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} {...props}>
      {icon ? <span className={styles.icon}>{icon}</span> : null}
      {children}
    </button>
  );
};
