import type { PostgrestError } from '@supabase/supabase-js';

const CACHE_NAMESPACE = 'supabase-query-cache';
const CACHE_VERSION = 'v1';
const CACHE_TTL_MS = 3 * 60 * 60 * 1000; // 3 hours

type CacheKeyPrimitive = string | number | boolean | null;
export type CacheKeyInput =
  | CacheKeyPrimitive
  | CacheKeyInput[]
  | { [key: string]: CacheKeyInput };

interface CacheEntry<TResult> {
  timestamp: number;
  result: TResult;
}

const memoryCache = new Map<string, CacheEntry<unknown>>();

const hasWindowStorage = (): boolean =>
  typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';

const toStorageKey = (key: string): string =>
  `${CACHE_NAMESPACE}:${CACHE_VERSION}:${key}`;

const isExpired = (timestamp: number): boolean =>
  Date.now() - timestamp > CACHE_TTL_MS;

const cloneResult = <T>(value: T): T => {
  if (value === null || typeof value !== 'object') {
    return value;
  }
  if (typeof structuredClone === 'function') {
    return structuredClone(value);
  }
  try {
    return JSON.parse(JSON.stringify(value));
  } catch {
    return value;
  }
};

const shouldCacheResult = (result: unknown): boolean => {
  if (!result || typeof result !== 'object') {
    return false;
  }
  const maybeError = (result as { error?: PostgrestError | null }).error;
  return !maybeError;
};

const loadFromMemory = <T>(key: string): T | null => {
  const entry = memoryCache.get(key);
  if (!entry || isExpired(entry.timestamp)) {
    if (entry) {
      memoryCache.delete(key);
    }
    return null;
  }
  return cloneResult(entry.result) as T;
};

const loadFromStorage = <T>(key: string): T | null => {
  if (!hasWindowStorage()) {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(toStorageKey(key));
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as CacheEntry<T>;
    if (!parsed || isExpired(parsed.timestamp)) {
      window.localStorage.removeItem(toStorageKey(key));
      return null;
    }
    memoryCache.set(key, parsed);
    return cloneResult(parsed.result);
  } catch {
    return null;
  }
};

const persistResult = <T>(key: string, entry: CacheEntry<T>, persist: boolean): void => {
  memoryCache.set(key, entry as CacheEntry<unknown>);
  if (!persist || !hasWindowStorage()) {
    return;
  }
  try {
    window.localStorage.setItem(toStorageKey(key), JSON.stringify(entry));
  } catch {
    // Swallow storage errors (quota exceeded, etc.)
  }
};

const removePersisted = (key: string): void => {
  memoryCache.delete(key);
  if (!hasWindowStorage()) {
    return;
  }
  try {
    window.localStorage.removeItem(toStorageKey(key));
  } catch {
    // ignore
  }
};

const stableStringify = (value: CacheKeyInput): string => {
  if (value === null || typeof value !== 'object') {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(',')}]`;
  }
  const entries = Object.entries(value).sort(([a], [b]) =>
    a.localeCompare(b),
  );
  return `{${entries
    .map(([k, v]) => `${JSON.stringify(k)}:${stableStringify(v)}`)
    .join(',')}}`;
};

export const createCacheKey = (
  table: string,
  descriptor: CacheKeyInput,
  scope = 'select',
): string => stableStringify({ table, descriptor, scope });

interface CachedQueryOptions<TResult> {
  key: string;
  query: () => PromiseLike<TResult>;
  forceFresh?: boolean;
  persist?: boolean;
}

export async function cachedQuery<TResult>({
  key,
  query,
  forceFresh = false,
  persist = true,
}: CachedQueryOptions<TResult>): Promise<TResult> {
  if (!forceFresh) {
    const fromMemory = loadFromMemory<TResult>(key);
    if (fromMemory !== null) {
      return fromMemory;
    }

    const fromStorage = loadFromStorage<TResult>(key);
    if (fromStorage !== null) {
      return fromStorage;
    }
  }

  const result = await query();
  if (shouldCacheResult(result)) {
    const entry: CacheEntry<TResult> = {
      timestamp: Date.now(),
      result: cloneResult(result),
    };
    persistResult(key, entry, persist);
  }

  return result;
}

export const invalidateCachedQuery = (key: string): void => {
  removePersisted(key);
};

export const clearQueryCache = (): void => {
  memoryCache.clear();
  if (!hasWindowStorage()) {
    return;
  }
  try {
    const prefix = `${CACHE_NAMESPACE}:${CACHE_VERSION}:`;
    const removalKeys: string[] = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const storageKey = window.localStorage.key(i);
      if (storageKey && storageKey.startsWith(prefix)) {
        removalKeys.push(storageKey);
      }
    }
    removalKeys.forEach((storageKey) => window.localStorage.removeItem(storageKey));
  } catch {
    // ignore
  }
};

export const getCacheTtlMs = (): number => CACHE_TTL_MS;
