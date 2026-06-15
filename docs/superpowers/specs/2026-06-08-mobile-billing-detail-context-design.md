# Mobile Billing Detail Context Design

## Goal

Add minimal state sharing between the mobile billing list and billing detail pages so that:

- Returning from detail restores the list filters and page.
- Detail supports `上一条` / `下一条` within the current filtered page result.
- The implementation stays isolated inside `src-mobile` and does not change PC code or backend contracts.

## Scope

In scope:

- Add a mobile-only Pinia store for billing list context.
- Restore billing list query state from the store on page entry.
- Persist current page bill ids and the selected row index when navigating to detail.
- Use the persisted ids for previous/next navigation inside detail.

Out of scope:

- Cross-page previous/next navigation.
- Pixel-perfect scroll position restoration.
- Backend API changes.
- Reusable generic state persistence infrastructure.

## Chosen Approach

Use a dedicated mobile Pinia store as the single shared context for the billing list and billing detail pages.

Why this approach:

- It keeps the URL clean on mobile.
- It avoids adding session storage synchronization logic.
- It is heavier than route query state, but still small and contained if the store only serves billing.

## Store Shape

Create `src-mobile/stores/billingContext.ts` with only the fields needed by this flow:

```ts
type BillingContextState = {
  page: number
  status: string
  q: string
  dateFrom: string
  dateTo: string
  billIds: number[]
  currentIndex: number
}
```

Required actions:

- `restoreListState()`: returns the current list filters and page.
- `setListState(payload)`: updates page and filter state.
- `setPageBills(ids, currentIndex?)`: stores the current page result ids and optional selected index.
- `setCurrentIndex(index)`: updates the active item index.
- `resetNavigation()`: clears `billIds` and `currentIndex` when the stored context is no longer usable.

The store must remain billing-specific. No abstraction for other pages.

## Billing List Behavior

`src-mobile/pages/Billing.vue` changes:

1. On mount, read the saved `page`, `status`, `q`, `dateFrom`, and `dateTo` from the store before the first fetch.
2. After each successful fetch, update the store with the latest list state and current page `billIds`.
3. When a bill row is tapped, compute its index within the current page result, write it to the store, and navigate to detail.
4. Existing fetch and filter behavior stays the same unless required to restore the saved state.

## Billing Detail Behavior

`src-mobile/pages/BillingDetail.vue` changes:

1. Keep the existing detail fetch by `billId`.
2. Read `billIds` and `currentIndex` from the store.
3. Show `上一条` and `下一条` buttons only when the adjacent id exists inside `billIds`.
4. Previous/next navigation updates `currentIndex`, pushes the new detail route, and refetches the selected bill.
5. The return action uses `router.push('/billing')` so the list rebuilds itself from the saved store state instead of depending on browser history.

## Failure Handling

- If the detail page is opened without usable billing context, keep the current detail fetch behavior.
- In that case, hide `上一条` / `下一条` and keep only the return action.
- If the current `billId` is not found in `billIds`, keep the detail visible and disable list-based navigation.

## Verification

Success criteria:

1. Open mobile billing list, apply filters, move to page `N`, enter a bill, return, and see the same page and filters restored.
2. Inside detail, `上一条` / `下一条` moves only within the current page result set.
3. Directly opening `/billing/:id` still loads the bill detail without crashing.
4. No backend files or PC frontend files are modified for this feature.
