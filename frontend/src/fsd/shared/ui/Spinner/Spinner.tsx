import styles from "./Spinner.module.scss";

type SpinnerProps = {
  label?: string;
};

export const Spinner = ({ label }: SpinnerProps) => {
  return (
    <div className={styles.wrapper}>
      <span className={styles.spinner} />
      {label ? <span className={styles.label}>{label}</span> : null}
    </div>
  );
};
