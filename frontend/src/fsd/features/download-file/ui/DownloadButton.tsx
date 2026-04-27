"use client";

import { useState } from "react";

import { Button } from "@/src/fsd/shared/ui/Button/Button";
import { getErrorMessage } from "@/src/fsd/shared/lib/apiError";
import {
  downloadFileFromManifest,
  saveBlob,
  type DownloadProgress,
} from "@/src/fsd/shared/lib/download";
import { useLazyGetDownloadManifestQuery } from "@/src/fsd/entities/file/api/dfsApi";

import styles from "./DownloadButton.module.scss";

type DownloadButtonProps = {
  fileId: number;
  disabled?: boolean;
};

export const DownloadButton = ({ fileId, disabled }: DownloadButtonProps) => {
  const [getManifest, manifestState] = useLazyGetDownloadManifestQuery();
  const [progress, setProgress] = useState<DownloadProgress | null>(null);
  const [error, setError] = useState("");

  const handleDownload = async () => {
    setError("");
    setProgress(null);

    try {
      const manifest = await getManifest(fileId).unwrap();
      const blob = await downloadFileFromManifest(manifest, setProgress);
      saveBlob(blob, manifest.file_name);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const isBusy = manifestState.isFetching;

  return (
    <div className={styles.wrapper}>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={handleDownload}
        disabled={disabled || isBusy}
      >
        {isBusy ? "Preparing..." : "Download"}
      </Button>
      {progress ? (
        <div className={styles.progress}>
          <div
            className={styles.bar}
            style={{ width: `${progress.percent}%` }}
          />
          <span>{progress.percent}%</span>
        </div>
      ) : null}
      {error ? <span className={styles.error}>{error}</span> : null}
    </div>
  );
};
