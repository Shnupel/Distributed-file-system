import { api } from "@/src/fsd/shared/api/api";
import type { UserRead } from "../model/types";

export const userApi = api.injectEndpoints({
  endpoints: (builder) => ({
    aboutMe: builder.query<UserRead, void>({
      query: () => "/about_me",
      providesTags: ["Me"],
    }),
  }),
});

export const { useAboutMeQuery } = userApi;
