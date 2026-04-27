import type { FetchBaseQueryError } from "@reduxjs/toolkit/query";

type ErrorWithMessage = {
  message?: string;
};

type ErrorPayload = {
  detail?: string | { message?: string } | Array<{ msg?: string }>;
};

export const getErrorMessage = (error: unknown) => {
  if (!error) {
    return "";
  }

  if (typeof error === "string") {
    return error;
  }

  if (typeof error === "object" && "data" in error) {
    const apiError = error as FetchBaseQueryError;
    const data = apiError.data as ErrorPayload | string | undefined;

    if (typeof data === "string") {
      return data;
    }

    if (data?.detail) {
      if (typeof data.detail === "string") {
        return data.detail;
      }
      if (Array.isArray(data.detail) && data.detail[0]?.msg) {
        return data.detail[0]?.msg || "Request failed";
      }
      if (typeof data.detail === "object" && "message" in data.detail) {
        return data.detail.message || "Request failed";
      }
    }
  }

  if (typeof error === "object" && "message" in error) {
    return (error as ErrorWithMessage).message || "Request failed";
  }

  return "Request failed";
};
