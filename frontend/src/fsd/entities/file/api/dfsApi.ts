import { api } from "@/src/fsd/shared/api/api";
import type {
  DownloadManifestRead,
  FileDeleteRead,
  FileSystemEntry,
  FileUploadRead,
} from "../model/types";

type ListEntriesArgs = {
  parentId?: number | null;
};

type UploadFileArgs = {
  file: File;
  parentId?: number | null;
};

type DeleteFileArgs = {
  fileId: number;
  parentId?: number | null;
};

export const dfsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    listEntries: builder.query<FileSystemEntry[], ListEntriesArgs>({
      query: ({ parentId }) => ({
        url: "/dfs/entries",
        params: parentId ? { parent_id: parentId } : undefined,
      }),
      providesTags: (_result, _error, arg) => [
        { type: "Entries", id: arg.parentId ?? "root" },
      ],
    }),
    uploadFile: builder.mutation<FileUploadRead, UploadFileArgs>({
      query: ({ file, parentId }) => {
        const form = new FormData();
        form.append("file", file);
        if (parentId) {
          form.append("parent_id", String(parentId));
        }
        return {
          url: "/dfs/files/upload",
          method: "POST",
          body: form,
        };
      },
      invalidatesTags: (_result, _error, arg) => [
        { type: "Entries", id: arg.parentId ?? "root" },
      ],
    }),
    deleteFile: builder.mutation<FileDeleteRead, DeleteFileArgs>({
      query: ({ fileId }) => ({
        url: `/dfs/files/${fileId}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, arg) => [
        { type: "Entries", id: arg.parentId ?? "root" },
      ],
    }),
    getDownloadManifest: builder.query<DownloadManifestRead, number>({
      query: (fileId) => `/dfs/files/${fileId}/manifest`,
    }),
  }),
});

export const {
  useListEntriesQuery,
  useUploadFileMutation,
  useDeleteFileMutation,
  useLazyGetDownloadManifestQuery,
} = dfsApi;
