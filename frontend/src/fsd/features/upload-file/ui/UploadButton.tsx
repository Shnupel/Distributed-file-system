"use client";

import { useRef, useState } from "react";

import { Button } from "@/src/fsd/shared/ui/Button/Button";
import { getErrorMessage } from "@/src/fsd/shared/lib/apiError";
import { useUploadFileMutation } from "@/src/fsd/entities/file/api/dfsApi";

import styles from "./UploadButton.module.scss";

type UploadButtonProps = {
  parentId?: number | null;
};

export const UploadButton = ({ parentId }: UploadButtonProps) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [error, setError] = useState("");
  const [uploadFile, uploadState] = useUploadFileMutation();

  const handlePick = () => {
    inputRef.current?.click();
  };

  const handleChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const files = event.target.files;
    if (!files?.length) {
      return;
    }

    setError("");

    try {
      for (const file of Array.from(files)) {
        await uploadFile({ file, parentId }).unwrap();
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  };

  return (
    <div className={styles.wrapper}>
      <Button
        type="button"
        variant="outline"
        onClick={handlePick}
        disabled={uploadState.isLoading}
      >
        {uploadState.isLoading ? "Uploading..." : "Upload files"}
      </Button>
      <input
        ref={inputRef}
        className={styles.input}
        type="file"
        multiple
        onChange={handleChange}
      />
      {error ? <span className={styles.error}>{error}</span> : null}
    </div>
  );
};
