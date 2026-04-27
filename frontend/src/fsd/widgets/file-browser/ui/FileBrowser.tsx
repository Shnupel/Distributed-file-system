"use client";

import { useMemo, useState } from "react";

import styles from "./FileBrowser.module.scss";
import { useListEntriesQuery } from "@/src/fsd/entities/file/api/dfsApi";
import type { FileSystemEntry } from "@/src/fsd/entities/file/model/types";
import { UploadButton } from "@/src/fsd/features/upload-file/ui/UploadButton";
import { DownloadButton } from "@/src/fsd/features/download-file/ui/DownloadButton";
import { Button } from "@/src/fsd/shared/ui/Button/Button";
import { Spinner } from "@/src/fsd/shared/ui/Spinner/Spinner";
import { formatBytes, formatDate } from "@/src/fsd/shared/lib/format";

const sortEntries = (entries: FileSystemEntry[]) => {
  return [...entries].sort((a, b) => {
    if (a.is_dir && !b.is_dir) {
      return -1;
    }
    if (!a.is_dir && b.is_dir) {
      return 1;
    }
    return a.name.localeCompare(b.name);
  });
};

type Crumb = { id: number; name: string };

export const FileBrowser = () => {
  const [path, setPath] = useState<Crumb[]>([]);
  const parentId = path.length ? path[path.length - 1].id : null;

  const { data, isFetching, isError, refetch } = useListEntriesQuery({
    parentId,
  });

  const entries = useMemo(
    () => (data ? sortEntries(data) : []),
    [data],
  );

  const handleOpenDir = (entry: FileSystemEntry) => {
    if (!entry.is_dir) {
      return;
    }
    setPath((prev) => [...prev, { id: entry.id, name: entry.name }]);
  };

  const handleBack = () => {
    setPath((prev) => prev.slice(0, -1));
  };

  const handleCrumb = (index: number) => {
    if (index < 0) {
      setPath([]);
      return;
    }
    setPath((prev) => prev.slice(0, index + 1));
  };

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>Your workspace</p>
          <h3 className={styles.title}>Files and folders</h3>
        </div>
        <div className={styles.actions}>
          <UploadButton parentId={parentId} />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </div>
      </div>

      <div className={styles.breadcrumbs}>
        <button
          type="button"
          className={styles.crumb}
          onClick={() => handleCrumb(-1)}
        >
          Root
        </button>
        {path.map((crumb, index) => (
          <button
            key={crumb.id}
            type="button"
            className={styles.crumb}
            onClick={() => handleCrumb(index)}
          >
            {crumb.name}
          </button>
        ))}
      </div>

      {path.length > 0 && (
        <Button type="button" variant="ghost" size="sm" onClick={handleBack}>
          Go up
        </Button>
      )}

      {isFetching ? (
        <div className={styles.state}>
          <Spinner label="Syncing directory" />
        </div>
      ) : null}

      {isError ? (
        <div className={styles.state}>Unable to load entries.</div>
      ) : null}

      {!isFetching && !entries.length ? (
        <div className={styles.empty}>
          <p>No files here yet. Upload something to get started.</p>
        </div>
      ) : null}

      {entries.length > 0 && (
        <div className={styles.list}>
          <div className={styles.rowHead}>
            <span>Name</span>
            <span>Type</span>
            <span>Size</span>
            <span>Updated</span>
            <span>Actions</span>
          </div>
          {entries.map((entry) => (
            <div key={entry.id} className={styles.row}>
              <button
                type="button"
                className={styles.name}
                onClick={() => handleOpenDir(entry)}
              >
                <span className={styles.icon}>
                  {entry.is_dir ? "DIR" : "FILE"}
                </span>
                {entry.name}
              </button>
              <span className={styles.meta}>
                {entry.is_dir
                  ? "Directory"
                  : entry.status !== "ready"
                    ? `File (${entry.status})`
                    : entry.mime_type || "File"}
              </span>
              <span className={styles.meta}>
                {entry.is_dir ? "-" : formatBytes(entry.size)}
              </span>
              <span className={styles.meta}>{formatDate(entry.updated_at)}</span>
              <span className={styles.actionsCell}>
                {entry.is_dir ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleOpenDir(entry)}
                  >
                    Open
                  </Button>
                ) : (
                  <DownloadButton
                    fileId={entry.id}
                    disabled={entry.status !== "ready"}
                  />
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
