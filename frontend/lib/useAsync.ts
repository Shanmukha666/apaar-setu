"use client";
import { useCallback, useEffect, useState } from "react";

interface AsyncState<T> { key: string; data: T | null; error: string | null }

/**
 * Run an async loader whenever `key` changes (put every input of the loader into the key).
 * `loading` is derived, so no state is set synchronously inside the effect.
 */
export function useAsync<T>(key: string, loader: () => Promise<T>) {
  const [version, setVersion] = useState(0);
  const [state, setState] = useState<AsyncState<T>>({ key: "", data: null, error: null });
  const fullKey = `${key}#${version}`;

  useEffect(() => {
    let cancelled = false;
    loader()
      .then((data) => { if (!cancelled) setState({ key: fullKey, data, error: null }); })
      .catch((e: unknown) => { if (!cancelled) setState({ key: fullKey, data: null, error: e instanceof Error ? e.message : "Something went wrong" }); });
    return () => { cancelled = true; };
    // The loader is recreated every render; `fullKey` is the single source of truth for when to reload.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullKey]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  const settled = state.key === fullKey;
  return { data: settled ? state.data : null, error: settled ? state.error : null, loading: !settled, reload };
}
