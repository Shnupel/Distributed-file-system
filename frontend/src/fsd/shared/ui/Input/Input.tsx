import type { InputHTMLAttributes } from "react";

import styles from "./Input.module.scss";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
};

export const Input = ({ label, hint, className, ...props }: InputProps) => {
  return (
    <label className={`${styles.field} ${className || ""}`.trim()}>
      {label ? <span className={styles.label}>{label}</span> : null}
      <input className={styles.input} {...props} />
      {hint ? <span className={styles.hint}>{hint}</span> : null}
    </label>
  );
};
