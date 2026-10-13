import { useEffect, useState } from "react";
import { ApiError } from "../lib/api";

export interface AsyncState<T> {
  loading: boolean;
  data?: T;
  error?: string;
}

function message(err: unknown): string {
  if (err instanceof ApiError) {
    return err.detail ? `${err.message}: ${err.detail}` : err.message;
  }
  return err instanceof Error ? err.message : String(err);
}

/** Run an async function on mount / when `deps` change, tracking loading/data/error. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ loading: true });

  useEffect(() => {
    let active = true;
    setState({ loading: true });
    fn()
      .then((data) => active && setState({ loading: false, data }))
      .catch((err) => active && setState({ loading: false, error: message(err) }));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
