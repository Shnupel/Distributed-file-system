"use client";

import { Provider } from "react-redux";
import { useRef } from "react";

import type { AppStore } from "./store";
import { makeStore } from "./store";

export default function Providers({
  children,
}: {
  children: React.ReactNode;
}) {
  const storeRef = useRef<AppStore | null>(null);
  const store = storeRef.current ?? (storeRef.current = makeStore());

  return <Provider store={store}>{children}</Provider>;
}
