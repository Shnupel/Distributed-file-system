import { useSyncExternalStore } from "react";

const STORAGE_KEY = "dfs_access_token";
let accessToken = "";
const listeners = new Set<() => void>();

const notify = () => {
  listeners.forEach((listener) => listener());
};

const readStorage = () => {
  if (typeof window === "undefined") {
    return accessToken;
  }

  const stored = sessionStorage.getItem(STORAGE_KEY) || "";
  if (stored && stored !== accessToken) {
    accessToken = stored;
  }
  return accessToken;
};

export const getAccessToken = () => readStorage();

export const setAccessToken = (token: string) => {
  accessToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      sessionStorage.setItem(STORAGE_KEY, token);
    } else {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  }
  notify();
};

export const clearAccessToken = () => setAccessToken("");

export const subscribeAccessToken = (listener: () => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

export const useAccessToken = () =>
  useSyncExternalStore(subscribeAccessToken, getAccessToken, () => "");
