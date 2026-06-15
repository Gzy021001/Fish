# Mobile Billing Detail Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mobile-only billing context persistence so the billing list restores filters/page after returning from detail, and detail supports previous/next inside the current page result.

**Architecture:** Keep all changes inside `src-mobile`. Add one focused Pinia store for billing context, hydrate `Billing.vue` from that store, and let `BillingDetail.vue` use stored `billIds/currentIndex` for navigation. Do not touch backend APIs or PC-side files.

**Tech Stack:** Vue 3, Pinia, Vue Router, TypeScript, Vite

---

## File Map

- Create: `d:\Fish\src-mobile\stores\billingContext.ts`
- Modify: `d:\Fish\src-mobile\pages\Billing.vue`
- Modify: `d:\Fish\src-mobile\pages\BillingDetail.vue`
- Verify: `d:\Fish\docs\superpowers\specs\2026-06-08-mobile-billing-detail-context-design.md`

Notes:

- The project currently has no dedicated mobile frontend test runner.
- Use `npm run check` as the first failure gate for missing imports/types.
- Use `npx vite --config d:\Fish\vite.mobile.config.ts build` for integration verification.

### Task 1: Add Billing Context Store

**Files:**
- Create: `d:\Fish\src-mobile\stores\billingContext.ts`
- Modify: `d:\Fish\src-mobile\pages\Billing.vue`

- [ ] **Step 1: Write the failing integration hook in `Billing.vue`**

Add the store import and the initial restore call before the store exists yet:

```ts
import { useBillingContextStore } from '../stores/billingContext'

const billingContextStore = useBillingContextStore()

const restoreStateFromContext = () => {
  const saved = billingContextStore.restoreListState()
  currentPage.value = saved.page
  status.value = saved.status
  searchText.value = saved.q
  dateFrom.value = saved.dateFrom
  dateTo.value = saved.dateTo
}
```

- [ ] **Step 2: Run type-check to verify it fails**

Run:

```bash
npm run check
```

Expected: FAIL with an error similar to `Cannot find module '../stores/billingContext'`.

- [ ] **Step 3: Write the minimal store implementation**

Create `d:\Fish\src-mobile\stores\billingContext.ts`:

```ts
import { defineStore } from 'pinia'

type BillingListState = {
  page: number
  status: string
  q: string
  dateFrom: string
  dateTo: string
}

type BillingContextState = BillingListState & {
  billIds: number[]
  currentIndex: number
}

const getDefaultState = (): BillingContextState => ({
  page: 1,
  status: '',
  q: '',
  dateFrom: '',
  dateTo: '',
  billIds: [],
  currentIndex: -1,
})

export const useBillingContextStore = defineStore('mobile-billing-context', {
  state: (): BillingContextState => getDefaultState(),
  actions: {
    restoreListState(): BillingListState {
      return {
        page: this.page,
        status: this.status,
        q: this.q,
        dateFrom: this.dateFrom,
        dateTo: this.dateTo,
      }
    },
    setListState(payload: BillingListState) {
      this.page = payload.page
      this.status = payload.status
      this.q = payload.q
      this.dateFrom = payload.dateFrom
      this.dateTo = payload.dateTo
    },
    setPageBills(ids: number[], currentIndex = -1) {
      this.billIds = ids
      this.currentIndex = currentIndex
    },
    setCurrentIndex(index: number) {
      this.currentIndex = index
    },
    resetNavigation() {
      this.billIds = []
      this.currentIndex = -1
    },
  },
})
```

- [ ] **Step 4: Finish the minimal `Billing.vue` store wiring**

Update `d:\Fish\src-mobile\pages\Billing.vue` so fetch success persists context and row click records the index:

```ts
const restoreStateFromContext = () => {
  const saved = billingContextStore.restoreListState()
  currentPage.value = saved.page
  status.value = saved.status
  searchText.value = saved.q
  dateFrom.value = saved.dateFrom
  dateTo.value = saved.dateTo
}

const syncListState = () => {
  billingContextStore.setListState({
    page: currentPage.value,
    status: status.value,
    q: searchText.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
  })
}

const syncPageBills = () => {
  billingContextStore.setPageBills(bills.value.map(item => item.id))
}

const goToDetail = (billId: number) => {
  const currentIndex = bills.value.findIndex(item => item.id === billId)
  billingContextStore.setListState({
    page: currentPage.value,
    status: status.value,
    q: searchText.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
  })
  billingContextStore.setPageBills(
    bills.value.map(item => item.id),
    currentIndex,
  )
  router.push(`/billing/${billId}`)
}
```

Also:

- call `restoreStateFromContext()` before the first `fetchBills()`
- call `syncListState()` and `syncPageBills()` after successful list fetch

- [ ] **Step 5: Run type-check to verify it passes**

Run:

```bash
npm run check
```

Expected: PASS with no TypeScript errors from `billingContext.ts` or `Billing.vue`.

- [ ] **Step 6: Commit**

```bash
git add d:\Fish\src-mobile\stores\billingContext.ts d:\Fish\src-mobile\pages\Billing.vue
git commit -m "feat: persist mobile billing list context"
```

### Task 2: Add Detail Previous/Next Navigation

**Files:**
- Modify: `d:\Fish\src-mobile\pages\BillingDetail.vue`

- [ ] **Step 1: Write the failing detail navigation hook**

Add the store usage and previous/next computed references before the detail page is fully wired:

```ts
import { watch, computed, onMounted, ref } from 'vue'
import { useBillingContextStore } from '../stores/billingContext'

const billingContextStore = useBillingContextStore()

const billIds = computed(() => billingContextStore.billIds)
const currentIndex = computed(() => billingContextStore.currentIndex)
const previousBillId = computed(() => {
  return currentIndex.value > 0 ? billIds.value[currentIndex.value - 1] : null
})
const nextBillId = computed(() => {
  return currentIndex.value >= 0 && currentIndex.value < billIds.value.length - 1
    ? billIds.value[currentIndex.value + 1]
    : null
})
```

- [ ] **Step 2: Run type-check to verify it fails if `watch`-driven route refetch is not wired yet**

Run:

```bash
npm run check
```

Expected: FAIL with an error similar to an unused or missing navigation handler while the template references `goPrevious`, `goNext`, or the new computed ids.

- [ ] **Step 3: Implement the minimal detail navigation**

Update `d:\Fish\src-mobile\pages\BillingDetail.vue`:

```ts
const goBackToList = () => {
  router.push('/billing')
}

const goPrevious = () => {
  if (!previousBillId.value) return
  billingContextStore.setCurrentIndex(currentIndex.value - 1)
  router.push(`/billing/${previousBillId.value}`)
}

const goNext = () => {
  if (!nextBillId.value) return
  billingContextStore.setCurrentIndex(currentIndex.value + 1)
  router.push(`/billing/${nextBillId.value}`)
}

watch(
  () => route.params.id,
  () => {
    fetchBillDetail()
  }
)
```

Update the template header/actions to use:

```vue
<button @click="goBackToList">返回</button>
<button :disabled="!previousBillId" @click="goPrevious">上一条</button>
<button :disabled="!nextBillId" @click="goNext">下一条</button>
```

Behavior rules:

- Hide or disable previous/next when no adjacent id exists.
- Keep direct detail access working even when `billIds` is empty.

- [ ] **Step 4: Run type-check to verify it passes**

Run:

```bash
npm run check
```

Expected: PASS with no errors from `BillingDetail.vue`.

- [ ] **Step 5: Build the mobile bundle**

Run:

```bash
npx vite --config d:\Fish\vite.mobile.config.ts build
```

Expected: PASS and emit/update `dist-mobile`.

- [ ] **Step 6: Commit**

```bash
git add d:\Fish\src-mobile\pages\BillingDetail.vue
git commit -m "feat: add mobile billing detail navigation"
```

### Task 3: Manual Verification Pass

**Files:**
- Modify: `d:\Fish\src-mobile\pages\Billing.vue`
- Modify: `d:\Fish\src-mobile\pages\BillingDetail.vue`

- [ ] **Step 1: Start the mobile dev server**

Run:

```bash
powershell -ExecutionPolicy Bypass -File d:\Fish\scripts\run-mobile-dev.ps1
```

Expected: Vite serves the mobile app on `http://localhost:5176/`.

- [ ] **Step 2: Verify list restoration manually**

Use this scenario:

1. Open `/billing`
2. Set a status filter
3. Enter a keyword
4. Change to page 2 if available
5. Open a bill detail
6. Tap `返回`

Expected:

- status filter stays restored
- keyword stays restored
- page stays restored
- list reloads with the same result slice

- [ ] **Step 3: Verify previous/next manually**

Use this scenario:

1. Open a bill from a page with at least 3 items
2. Tap `下一条`
3. Tap `上一条`

Expected:

- the detail route id changes
- the detail content refetches correctly
- navigation stops at the page boundaries

- [ ] **Step 4: Verify direct detail fallback manually**

Open a detail route directly in a fresh tab:

```text
/#/billing/33
```

Expected:

- detail still loads
- previous/next stay unavailable without stored context
- return button still leads back to `/billing`

- [ ] **Step 5: Final commit**

```bash
git add d:\Fish\src-mobile\pages\Billing.vue d:\Fish\src-mobile\pages\BillingDetail.vue d:\Fish\src-mobile\stores\billingContext.ts
git commit -m "feat: restore mobile billing context"
```
