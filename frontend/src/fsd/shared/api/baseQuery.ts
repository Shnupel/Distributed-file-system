import type {
  BaseQueryFn,
  FetchArgs,
  FetchBaseQueryError,
} from "@reduxjs/toolkit/query";
import { fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { API_BASE_URL } from "../config/env";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "../lib/authToken";

type TokenResponse = {
  access_token: string;
  token_type?: string;
};

const rawBaseQuery = fetchBaseQuery({
  baseUrl: API_BASE_URL,
  credentials: "include",
  prepareHeaders: (headers) => {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
  },
});

const isRefreshCall = (args: string | FetchArgs) => {
  const url = typeof args === "string" ? args : String(args.url);
  return url.includes("/refresh");
};

export const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401 && !isRefreshCall(args)) {
    const refreshResult = await rawBaseQuery(
      { url: "/refresh", method: "POST" },
      api,
      extraOptions,
    );

    if (refreshResult.data && typeof refreshResult.data === "object") {
      const token = (refreshResult.data as TokenResponse).access_token;
      if (token) {
        setAccessToken(token);
        result = await rawBaseQuery(args, api, extraOptions);
      } else {
        clearAccessToken();
      }
    } else {
      clearAccessToken();
    }
  }

  return result;
};
