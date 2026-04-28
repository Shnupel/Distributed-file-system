import { api } from "@/src/fsd/shared/api/api";
import { setAccessToken } from "@/src/fsd/shared/lib/authToken";
import type { UserRead } from "@/src/fsd/entities/user/model/types";

import type { LoginPayload, RegisterPayload, TokenResponse } from "../model/types";

export const authApi = api.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation<TokenResponse, LoginPayload>({
      query: ({ username, password }) => ({
        url: "/login",
        method: "POST",
        body: new URLSearchParams({
          username,
          password,
        }),
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }),
      invalidatesTags: ["Me"],
      async onQueryStarted(_arg, { queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          if (data.access_token) {
            setAccessToken(data.access_token);
          }
        } catch {
          // handled by component
        }
      },
    }),
    register: builder.mutation<UserRead, RegisterPayload>({
      query: (payload) => ({
        url: "/register",
        method: "POST",
        body: payload,
      }),
    }),
    refresh: builder.mutation<TokenResponse, void>({
      query: () => ({
        url: "/refresh",
        method: "POST",
      }),
      invalidatesTags: ["Me"],
      async onQueryStarted(_arg, { queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          if (data.access_token) {
            setAccessToken(data.access_token);
          }
        } catch {
          // handled by caller
        }
      },
    }),
    logout: builder.mutation<{ message: string }, void>({
      query: () => ({
        url: "/logout",
        method: "POST",
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useRefreshMutation,
  useLogoutMutation,
} = authApi;
