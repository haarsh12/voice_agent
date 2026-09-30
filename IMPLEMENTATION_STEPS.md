# Implementation Steps - Performance Optimization

## Quick Start (5 minutes)

### Step 1: Test the Optimized Schemes View

**Option A: Side-by-side comparison**
Add a route to test the new component:

```typescript
// In App.tsx
import { SchemesViewOptimized } from './components/PortalViewsOptimized'

// Add new route
case '/schemes-fast':
  content = <SchemesViewOptimized onTalk={() => navigate('/voice')} profile={auth.user} />
  break
```

Then visit `/schemes-fast` to see the optimized version.

**Option B: Replace existing (recommended after testing)**

```typescript
// In App.tsx, replace the schemes case:
case '/schemes':
  content = <SchemesViewOptimized onTalk={() => navigate('/voice')} profile={auth.user} />
  break
```

### Step 2: Verify Knowledge Base Improvements

The `KnowledgeBasePanel` component has been automatically updated. Just navigate to `/knowledge-base` to see:
- Skeleton loaders on first visit
- Cached data on subsequent visits
- "Clear cache" button in header
- Progressive loading (6 sources initially)

### Step 3: Test Cache Functionality

1. **Visit schemes page** → should load from API (first time)
2. **Navigate away and back** → should load instantly from cache
3. **Wait 3 minutes** → cache expires, fresh fetch on next visit
4. **Click "Clear cache & reload"** → forces fresh data
5. **Use filters** → new queries bypass cache appropriately

## Full Integration Guide

### 1. Update Main App Component

Edit `frontend/src/App.tsx`:

```typescript
// Add imports at top
import { SchemesViewOptimized } from './components/PortalViewsOptimized'

// Update the schemes route
case '/schemes':
  content = <SchemesViewOptimized onTalk={() => navigate('/voice')} profile={auth.user} />
  break
```

### 2. Optional: Remove Old Component

Once confirmed working, you can remove the old `SchemesView` from `PortalViews.tsx` to keep codebase clean.

### 3. Adjust Cache TTLs (Optional)

Edit `frontend/src/lib/api.ts` if you want different cache durations:

```typescript
// Current values:
cache.set(cacheKey, result, { ttl: 3 * 60 * 1000 }) // Schemes: 3 min
cache.set(cacheKey, result, { ttl: 5 * 60 * 1000 }) // Detail: 5 min
cache.set(cacheKey, result, { ttl: 10 * 60 * 1000 }) // Filters: 10 min
cache.set(cacheKey, result, { ttl: 2 * 60 * 1000 }) // KB: 2 min

// Adjust as needed for your use case
```

### 4. Customize Skeleton Count

Edit `frontend/src/components/PortalViewsOptimized.tsx`:

```typescript
// Initial skeleton count (default: 6)
{Array.from({ length: 6 }).map((_, i) => (
  <SchemeCardSkeleton key={i} />
))}

// Loading more skeleton count (default: 3)
{Array.from({ length: 3 }).map((_, i) => (
  <SchemeCardSkeleton key={`more-${i}`} />
))}
```

### 5. Customize Page Size

Edit the `PAGE_SIZE` constant:

```typescript
const PAGE_SIZE = 18 // Change to 12, 24, 30, etc.
```

Note: This is just a constant for reference; the actual limit is passed to the API.

### 6. Add Cache Monitoring (Optional)

Add to your app initialization to monitor cache usage:

```typescript
// In App.tsx or main.tsx
import { cache } from './lib/cache'

useEffect(() => {
  const stats = cache.stats()
  console.log('📦 Cache Stats:', {
    entries: stats.count,
    size: `${(stats.totalSize / 1024).toFixed(2)} KB`,
    maxEntries: 50
  })
  
  // Optional: Periodic cleanup
  const interval = setInterval(() => {
    cache.clearExpired()
  }, 5 * 60 * 1000) // Every 5 minutes
  
  return () => clearInterval(interval)
}, [])
```

## Testing Checklist

### Schemes Page
- [ ] Initial load shows 18 schemes with skeleton loaders
- [ ] Cached data loads instantly on return visit
- [ ] "Load more" button appears when more schemes available
- [ ] "Load more" fetches next 18 schemes
- [ ] Skeleton loaders show while loading more
- [ ] "Clear cache & reload" forces fresh data
- [ ] Filters work correctly
- [ ] Search works correctly
- [ ] Scheme detail modal opens correctly
- [ ] Scheme detail uses cache

### Knowledge Base Page
- [ ] Metrics load with skeleton loaders initially
- [ ] Shows 6 sources initially
- [ ] "Show all X sources" button expands to full list
- [ ] Shows 10 documents initially in table
- [ ] "Show all X documents" button expands table
- [ ] "Clear cache" button works
- [ ] "Refresh" button bypasses cache
- [ ] Cached data loads instantly on return
- [ ] Source cards display correctly
- [ ] Document table displays correctly

### Cache Behavior
- [ ] First visit fetches from API
- [ ] Second visit within TTL uses cache
- [ ] Visit after TTL expiration fetches fresh
- [ ] Clear cache button removes all cached data
- [ ] Pagination doesn't cache subsequent pages
- [ ] localStorage quota errors handled gracefully

### Performance
- [ ] Initial page load < 1 second (cached)
- [ ] Initial page load < 2 seconds (uncached)
- [ ] "Load more" < 1 second
- [ ] No visible lag when scrolling
- [ ] Skeletons show smoothly without flicker
- [ ] No console errors

## Rollback Plan

If issues arise, you can quickly rollback:

### Rollback Schemes Page

```typescript
// In App.tsx, revert to original:
import { SchemesView } from './components/PortalViews'

case '/schemes':
  content = <SchemesView onTalk={() => navigate('/voice')} profile={auth.user} />
  break
```

### Rollback Knowledge Base

```bash
# Restore from git
git checkout HEAD -- frontend/src/components/KnowledgeBasePanel.tsx
```

Or manually remove:
- Import of `cache` and skeleton components
- `showAllSources` and `showAllDocuments` states
- Progressive loading logic
- Cache clear button

### Clear All Caches

If users report issues:

```typescript
// Add temporary button in your app
<button onClick={() => {
  localStorage.clear()
  sessionStorage.clear()
  window.location.reload()
}}>
  Clear All Data
</button>
```

## Production Deployment

### 1. Build and Test

```bash
cd frontend
npm run build
npm run preview  # Test production build locally
```

### 2. Check Bundle Size

The new code adds approximately:
- `cache.ts`: ~3 KB gzipped
- Skeleton components: ~2 KB gzipped
- Optimized views: ~5 KB gzipped
- **Total addition**: ~10 KB gzipped

### 3. Environment Variables

No new environment variables required. All caching is client-side.

### 4. Browser Support

Test in your target browsers:
- Chrome 90+: ✅
- Firefox 88+: ✅
- Safari 14+: ✅
- Edge 90+: ✅

### 5. Monitor After Deploy

Watch for:
- API request reduction (should see ~50-70% fewer requests)
- Page load time improvements
- User reports of stale data
- LocalStorage quota errors (rare)

## Configuration Options

### Cache TTLs by Data Freshness Need

```typescript
// Frequently changing data (low TTL)
cache.set(key, data, { ttl: 1 * 60 * 1000 }) // 1 minute

// Moderate change rate (medium TTL)
cache.set(key, data, { ttl: 5 * 60 * 1000 }) // 5 minutes

// Rarely changing data (high TTL)
cache.set(key, data, { ttl: 30 * 60 * 1000 }) // 30 minutes
```

### Pagination Settings

```typescript
// Conservative: Small pages, more clicks
const PAGE_SIZE = 12

// Balanced: Medium pages (current)
const PAGE_SIZE = 18

// Aggressive: Large pages, fewer clicks
const PAGE_SIZE = 30
```

### Progressive Loading Limits

```typescript
// Knowledge Base source limit
const visibleSources = showAllSources 
  ? knowledgeBase.sources 
  : knowledgeBase.sources.slice(0, 6) // Change 6 to your preference

// Document limit
const visibleDocuments = showAllDocuments 
  ? knowledgeBase.recent_documents 
  : knowledgeBase.recent_documents.slice(0, 10) // Change 10 to your preference
```

## Support and Troubleshooting

### Common Issues

**Issue**: Cache not clearing
**Solution**: Check browser localStorage permissions, try `cache.clear()` in console

**Issue**: Stale data showing
**Solution**: Reduce TTL values or add refresh button usage education

**Issue**: Quota exceeded error
**Solution**: Cache automatically cleans up, but you can manually reduce MAX_CACHE_SIZE in cache.ts

**Issue**: Skeletons flashing too quickly
**Solution**: Add minimum loading time with `setTimeout` in load functions

### Debug Mode

Add debug logging:

```typescript
// In cache.ts get() method
console.log('Cache hit:', key)

// In cache.ts set() method
console.log('Cache miss, storing:', key)

// In load functions
console.log('Loading with cache:', useCache)
```

### Getting Help

1. Check browser console for errors
2. Review `PERFORMANCE_OPTIMIZATION_GUIDE.md`
3. Check network tab to verify cache behavior
4. Test with cache disabled (DevTools → Application → Clear storage)

---

**Ready to go!** Start with testing the optimized components, then integrate fully once confirmed working.
