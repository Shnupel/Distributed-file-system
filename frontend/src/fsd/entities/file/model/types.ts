export type FileSystemEntry = {
  id: number;
  owner_id: number;
  parent_id: number | null;
  name: string;
  is_dir: boolean;
  size: number;
  mime_type: string | null;
  file_sha256: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type FileUploadRead = {
  file_id: number;
  file_name: string;
  size: number;
  chunks_count: number;
  file_sha256: string;
  status: string;
};

export type FileDeleteRead = {
  file_id: number;
  deleted: boolean;
};

export type ChunkReplicaUrl = {
  node_id: number;
  node_name: string;
  url: string;
};

export type ChunkManifest = {
  chunk_id: number;
  index: number;
  size: number;
  sha256: string;
  replicas: ChunkReplicaUrl[];
};

export type DownloadManifestRead = {
  file_id: number;
  file_name: string;
  size: number;
  file_sha256: string;
  expires_at_unix: number;
  chunks: ChunkManifest[];
};
