/**
 * Browser-side cache utility with TTL support for API responses.
 * Uses localStorage with automatic expiration and size management.
 */

export type CacheOptions = {
  /** Time-to-live in milliseconds. Default: 5 minutes */
  ttl?: number
  /** Whether to use sessionStorage instead of localStorage. Default: false */
  useSession?: boolean
}

type CacheEntry<T> = {
  data: T
  timestamp: number
  ttl: number
}

const DEFAULT_TTL = 5 * 60 * 1000 // 5 minutes
const CACHE_PREFIX = 'sahayak_cache_'
const MAX_CACHE_SIZE = 50 // Maximum number of cached entries

/**
 * Cache manager for storing and retrieving API responses
 */
export class CacheManager {
  private getStorage(useSession = false): Storage {
    return useSession ? sessionStorage : localStorage
  }

  private getKey(key: string): string {
    return `${CACHE_PREFIX}${key}`
  }

  /**
   * Store data in cache with TTL
   */
  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const { ttl = DEFAULT_TTL, useSession = false } = options
    const storage = this.getStorage(useSession)
    
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
    }

    try {
      storage.setItem(this.getKey(key), JSON.stringify(entry))
      this.enforceMaxSize(storage)
    } catch (error) {
      // Storage might be full or unavailable. Clean up and try once more.
      if (error instanceof Error && error.name === 'QuotaExceededError') {
        this.clear(useSession)
        try {
          storage.setItem(this.getKey(key), JSON.stringify(entry))
        } catch {
          // Silent fail if still can't store
        }
      }
    }
  }

  /**
   * Retrieve data from cache if not expired
   */
  get<T>(key: string, options: Pick<CacheOptions, 'useSession'> = {}): T | null {
    const { useSession = false } = options
    const storage = this.getStorage(useSession)
    
    try {
      const item = storage.getItem(this.getKey(key))
      if (!item) return null

      const entry: CacheEntry<T> = JSON.parse(item)
      const age = Date.now() - entry.timestamp

      // Check if expired
      if (age > entry.ttl) {
        this.delete(key, { useSession })
        return null
      }

      return entry.data
    } catch {
      // Invalid JSON or other error
      this.delete(key, { useSession })
      return null
    }
  }

  /**
   * Check if a key exists and is not expired
   */
  has(key: string, options: Pick<CacheOptions, 'useSession'> = {}): boolean {
    return this.get(key, options) !== null
  }

  /**
   * Delete a specific cache entry
   */
  delete(key: string, options: Pick<CacheOptions, 'useSession'> = {}): void {
    const { useSession = false } = options
    const storage = this.getStorage(useSession)
    storage.removeItem(this.getKey(key))
  }

  /**
   * Clear all cached entries
   */
  clear(useSession = false): void {
    const storage = this.getStorage(useSession)
    const keys = Object.keys(storage)
    
    keys.forEach((key) => {
      if (key.startsWith(CACHE_PREFIX)) {
        storage.removeItem(key)
      }
    })
  }

  /**
   * Clear all expired entries
   */
  clearExpired(useSession = false): void {
    const storage = this.getStorage(useSession)
    const keys = Object.keys(storage)
    
    keys.forEach((key) => {
      if (key.startsWith(CACHE_PREFIX)) {
        try {
          const item = storage.getItem(key)
          if (!item) return

          const entry: CacheEntry<unknown> = JSON.parse(item)
          const age = Date.now() - entry.timestamp

          if (age > entry.ttl) {
            storage.removeItem(key)
          }
        } catch {
          // Invalid entry, remove it
          storage.removeItem(key)
        }
      }
    })
  }

  /**
   * Enforce maximum cache size by removing oldest entries
   */
  private enforceMaxSize(storage: Storage): void {
    const entries: Array<{ key: string; timestamp: number }> = []

    Object.keys(storage).forEach((key) => {
      if (key.startsWith(CACHE_PREFIX)) {
        try {
          const item = storage.getItem(key)
          if (!item) return
          const entry: CacheEntry<unknown> = JSON.parse(item)
          entries.push({ key, timestamp: entry.timestamp })
        } catch {
          // Skip invalid entries
        }
      }
    })

    if (entries.length > MAX_CACHE_SIZE) {
      // Sort by timestamp (oldest first)
      entries.sort((a, b) => a.timestamp - b.timestamp)
      
      // Remove oldest entries
      const toRemove = entries.length - MAX_CACHE_SIZE
      for (let i = 0; i < toRemove; i++) {
        storage.removeItem(entries[i].key)
      }
    }
  }

  /**
   * Get cache statistics
   */
  stats(useSession = false): { count: number; totalSize: number } {
    const storage = this.getStorage(useSession)
    let count = 0
    let totalSize = 0

    Object.keys(storage).forEach((key) => {
      if (key.startsWith(CACHE_PREFIX)) {
        count++
        const item = storage.getItem(key)
        if (item) {
          totalSize += new Blob([item]).size
        }
      }
    })

    return { count, totalSize }
  }
}

// Singleton instance
export const cache = new CacheManager()

/**
 * Helper to create cached API calls
 */
export function withCache<T extends unknown[], R>(
  fn: (...args: T) => Promise<R>,
  getCacheKey: (...args: T) => string,
  options: CacheOptions = {}
): (...args: T) => Promise<R> {
  return async (...args: T): Promise<R> => {
    const cacheKey = getCacheKey(...args)
    
    // Check cache first
    const cached = cache.get<R>(cacheKey, options)
    if (cached !== null) {
      return cached
    }

    // Fetch fresh data
    const result = await fn(...args)
    
    // Store in cache
    cache.set(cacheKey, result, options)
    
    return result
  }
}
