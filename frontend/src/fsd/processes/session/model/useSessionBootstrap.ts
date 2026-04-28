"use client";

import { useEffect, useRef } from "react";

import { useRefreshMutation } from "@/src/fsd/features/auth/api/authApi";
import { useAccessToken } from "@/src/fsd/shared/lib/authToken";
import { useAboutMeQuery } from "@/src/fsd/entities/user/api/userApi";

export const useSessionBootstrap = () => {
  const accessToken = useAccessToken();
  const [refresh, refreshState] = useRefreshMutation();
  const hasTriedRef = useRef(false);

  useEffect(() => {
    if (!hasTriedRef.current && !accessToken) {
      hasTriedRef.current = true;
      refresh();
    }
  }, [accessToken, refresh]);

  const aboutMeQuery = useAboutMeQuery(undefined, { skip: !accessToken });

  const isLoading =
    refreshState.isLoading || (accessToken && aboutMeQuery.isFetching);

  return {
    accessToken,
    isLoading,
    user: aboutMeQuery.data ?? null,
    isAuthenticated: Boolean(accessToken && aboutMeQuery.data),
    error: refreshState.error || aboutMeQuery.error,
  };
};
