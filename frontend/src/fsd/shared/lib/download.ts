type ManifestReplica = {
  url: string;
};

type ManifestChunk = {
  index: number;
  size: number;
  sha256: string;
  replicas: ManifestReplica[];
};

type DownloadManifest = {
  file_name: string;
  size: number;
  chunks: ManifestChunk[];
};

export type DownloadProgress = {
  percent: number;
  downloadedBytes: number;
};

const toHex = (buffer: ArrayBuffer) =>
  Array.from(new Uint8Array(buffer))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");

const sha256Hex = async (buffer: ArrayBuffer) => {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return toHex(digest);
};

const downloadChunk = async (chunk: ManifestChunk) => {
  let lastError: Error | null = null;

  for (const replica of chunk.replicas) {
    try {
      const response = await fetch(replica.url, {
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`Chunk download failed (${response.status})`);
      }

      const buffer = await response.arrayBuffer();
      const hash = await sha256Hex(buffer);
      if (hash !== chunk.sha256) {
        throw new Error("Chunk checksum mismatch");
      }

      return buffer;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Download failed");
    }
  }

  throw lastError || new Error("All replicas failed");
};

export const downloadFileFromManifest = async (
  manifest: DownloadManifest,
  onProgress?: (progress: DownloadProgress) => void,
) => {
  const ordered = [...manifest.chunks].sort((a, b) => a.index - b.index);
  const buffers: ArrayBuffer[] = [];
  let downloadedBytes = 0;

  for (const chunk of ordered) {
    if (!chunk.replicas.length) {
      throw new Error("Chunk has no replicas");
    }

    const buffer = await downloadChunk(chunk);
    buffers.push(buffer);
    downloadedBytes += chunk.size;

    if (onProgress) {
      const percent = manifest.size
        ? Math.min(100, Math.round((downloadedBytes / manifest.size) * 100))
        : 100;
      onProgress({ percent, downloadedBytes });
    }
  }

  return new Blob(buffers, { type: "application/octet-stream" });
};

export const saveBlob = (blob: Blob, fileName: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName || "download.bin";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};
