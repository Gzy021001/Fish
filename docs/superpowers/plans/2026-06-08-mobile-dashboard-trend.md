# Mobile Dashboard Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the mobile dashboard sections `价格摘要` and `最近录入品种` with mobile versions of `周单价趋势` and `单价浮动`, while keeping all data sourcing inside the existing dashboard fetch flow.

**Architecture:** Keep the implementation inside `src-mobile/pages/Dashboard.vue`. Reuse the already-loaded `speciesList` and `trendMap`, add PC-aligned packaging filtering and two new computed lists, then replace the two template sections with mobile-compressed trend cards and fluctuation rows.

**Tech Stack:** Vue 3, TypeScript, Composition API, Axios, Vite

---

## File Map

- Modify: `d:\Fish\src-mobile\pages\Dashboard.vue`
- Verify: `d:\Fish\docs\superpowers\specs\2026-06-08-mobile-dashboard-trend-design.md`

Notes:

- This feature stays inside one mobile page by design.
- The repository currently does not have a dedicated mobile frontend unit test runner.
- Use `npm run check` and `npx vite --config d:\Fish\vite.mobile.config.ts build` as the verification gates.

### Task 1: Add New Mobile Dashboard Derived Data

**Files:**
- Modify: `d:\Fish\src-mobile\pages\Dashboard.vue`

- [ ] **Step 1: Write the failing type-level change**

Add references to the future computed fields in `Dashboard.vue` before defining them:

```ts
const weeklyTrendCards = computed(() => [])
const priceFluctuationRows = computed(() => [])
```

Then update the template headings so it references the new section names:

```vue
<h2 class="text-base font-serif text-[#6d4f32]">周单价趋势</h2>
<h2 class="text-base font-serif text-[#6d4f32]">单价浮动</h2>
```

- [ ] **Step 2: Run type-check to verify the current page still needs the new derived structures**

Run:

```bash
npm run check
```

Expected: PASS for the repo, but the page is still not behavior-complete because the new computed fields only return empty arrays. This is the red step for the behavior gap, not a syntax failure.

- [ ] **Step 3: Write the minimal derived data implementation**

Inside `d:\Fish\src-mobile\pages\Dashboard.vue`, add the same packaging filter intent as PC and the two new computed lists:

```ts
const isPackagingItem = (name: string) => {
  const keywords = ['袋', '打包', '包装', '绳子', '胶带', '泡沫', '保温', '耗材']
  return keywords.some(keyword => name.includes(keyword))
}

const weeklyTrendCards = computed(() => {
  return speciesList.value
    .map(species => {
      if (isPackagingItem(species.name_zh)) return null
      const points = [...(trendMap.value[species.id] || [])]
        .filter(point => point.date && point.avg_price != null)
        .sort((a, b) => a.date.localeCompare(b.date))

      if (points.length < 2) return null

      const start = points[0]
      const current = points[points.length - 1]
      const recentPoints = points.slice(-3).map((point, index, arr) => {
        const prev = index === 0 ? null : arr[index - 1]
        const diff = prev ? Number(point.avg_price) - Number(prev.avg_price) : 0
        return {
          date: formatDate(point.date),
          price: formatPrice(Number(point.avg_price)),
          diff,
          diffLabel: index === 0 ? '-' : `${diff >= 0 ? '+' : ''}${formatPrice(diff)}`,
        }
      })

      const changeValue = Number(current.avg_price) - Number(start.avg_price)

      return {
        id: species.id,
        name: species.name_zh,
        startDate: formatDate(start.date),
        endDate: formatDate(current.date),
        startPrice: formatPrice(Number(start.avg_price)),
        currentPrice: formatPrice(Number(current.avg_price)),
        changeValue,
        changeLabel: `${changeValue >= 0 ? '+' : ''}${formatPrice(changeValue)}`,
        recentPoints,
      }
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((a, b) => Math.abs(b.changeValue) - Math.abs(a.changeValue))
    .slice(0, 6)
})

const priceFluctuationRows = computed(() => {
  return speciesList.value
    .map(species => {
      if (isPackagingItem(species.name_zh)) return null
      const prices = (trendMap.value[species.id] || [])
        .map(point => Number(point.avg_price))
        .filter(price => !Number.isNaN(price))

      if (prices.length === 0) return null

      const minPrice = Math.min(...prices)
      const maxPrice = Math.max(...prices)

      return {
        id: species.id,
        name: species.name_zh,
        minPrice,
        maxPrice,
        rangeValue: maxPrice - minPrice,
      }
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((a, b) => b.rangeValue - a.rangeValue)
    .slice(0, 6)
})
```

- [ ] **Step 4: Run type-check to verify the derived data compiles**

Run:

```bash
npm run check
```

Expected: PASS with no new type errors from `Dashboard.vue`.

- [ ] **Step 5: Commit**

```bash
git add d:\Fish\src-mobile\pages\Dashboard.vue
git commit -m "feat: add mobile dashboard trend data"
```

### Task 2: Replace The Two Dashboard Sections

**Files:**
- Modify: `d:\Fish\src-mobile\pages\Dashboard.vue`

- [ ] **Step 1: Write the failing UI replacement**

Replace the old section titles and empty-state text first:

```vue
<h2 class="text-base font-serif text-[#6d4f32]">周单价趋势</h2>
<span class="text-xs text-[#8a6b4a]">最近趋势</span>
```

```vue
<h2 class="text-base font-serif text-[#6d4f32]">单价浮动</h2>
<span class="text-xs text-[#8a6b4a]">最高 - 最低</span>
```

And update the empty states:

```vue
暂无周单价趋势数据
暂无单价浮动数据
```

- [ ] **Step 2: Run the mobile build to capture the incomplete UI state**

Run:

```bash
npx vite --config d:\Fish\vite.mobile.config.ts build
```

Expected: PASS build-wise, but the page still shows the old row structure until the template body is replaced. This confirms the next step is still required.

- [ ] **Step 3: Write the minimal mobile-compressed template**

Replace the old `价格摘要` loop with a trend card loop:

```vue
<div v-else class="mt-3 space-y-3">
  <div
    v-for="item in weeklyTrendCards"
    :key="item.id"
    class="rounded-2xl border border-[#ead9bc] bg-[#fcf8f2] px-4 py-3"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="truncate text-sm font-semibold text-[#5c4033]">{{ item.name }}</p>
        <p class="mt-1 text-xs text-[#8a6b4a]">{{ item.startDate }} -> {{ item.endDate }}</p>
      </div>
      <p
        class="shrink-0 text-xs font-semibold"
        :class="item.changeValue >= 0 ? 'text-red-500' : 'text-green-600'"
      >
        {{ item.changeLabel }}
      </p>
    </div>

    <div class="mt-2 flex items-center justify-between text-xs text-[#8a6b4a]">
      <span>{{ item.startPrice }}</span>
      <span>-></span>
      <span class="font-semibold text-[#5c4033]">{{ item.currentPrice }}</span>
    </div>

    <div class="mt-3 space-y-1.5">
      <div
        v-for="point in item.recentPoints"
        :key="`${item.id}-${point.date}-${point.price}`"
        class="flex items-center justify-between rounded-xl bg-white/80 px-3 py-2 text-xs"
      >
        <span class="text-[#8a6b4a]">{{ point.date }}</span>
        <span class="tabular-nums text-[#5c4033]">{{ point.price }}</span>
        <span
          class="tabular-nums"
          :class="
            point.diff > 0
              ? 'text-red-500'
              : point.diff < 0
                ? 'text-green-600'
                : 'text-[#8a6b4a]'
          "
        >
          {{ point.diffLabel }}
        </span>
      </div>
    </div>
  </div>
</div>
```

Replace the old `最近录入品种` rows with fluctuation rows:

```vue
<div v-else class="mt-3 space-y-2">
  <div
    v-for="item in priceFluctuationRows"
    :key="item.id"
    class="rounded-2xl border border-[#f0e2ca] px-4 py-3"
  >
    <div class="flex items-center justify-between gap-3">
      <p class="truncate text-sm font-medium text-[#5c4033]">{{ item.name }}</p>
      <p class="text-xs font-semibold text-[#8b6914]">
        {{ formatPrice(item.rangeValue) }}
      </p>
    </div>
    <div class="mt-2 grid grid-cols-2 gap-3 text-xs">
      <div class="rounded-xl bg-[#fcf8f2] px-3 py-2">
        <p class="text-[#8a6b4a]">最低</p>
        <p class="mt-1 font-semibold text-[#5c4033]">{{ formatPrice(item.minPrice) }}</p>
      </div>
      <div class="rounded-xl bg-[#fcf8f2] px-3 py-2">
        <p class="text-[#8a6b4a]">最高</p>
        <p class="mt-1 font-semibold text-[#5c4033]">{{ formatPrice(item.maxPrice) }}</p>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 4: Run type-check and mobile build**

Run:

```bash
npm run check
npx vite --config d:\Fish\vite.mobile.config.ts build
```

Expected:

- both commands PASS
- the build emits updated `Dashboard-*.js` output in `dist-mobile`

- [ ] **Step 5: Commit**

```bash
git add d:\Fish\src-mobile\pages\Dashboard.vue
git commit -m "feat: update mobile dashboard trend sections"
```

### Task 3: Manual Verification

**Files:**
- Modify: `d:\Fish\src-mobile\pages\Dashboard.vue`

- [ ] **Step 1: Start or reuse the mobile dev server**

Run:

```bash
powershell -ExecutionPolicy Bypass -File d:\Fish\scripts\run-mobile-dev.ps1
```

Expected: the mobile app is available at `http://localhost:5176/mobile.html#/dashboard`.

- [ ] **Step 2: Verify the two section titles changed**

Manual check:

1. Open `/#/dashboard`
2. Confirm the old labels are gone

Expected:

- `价格摘要` no longer appears
- `最近录入品种` no longer appears
- `周单价趋势` appears
- `单价浮动` appears

- [ ] **Step 3: Verify trend card contents**

Manual check:

1. Inspect the first few `周单价趋势` cards
2. Confirm each card shows
   - species name
   - date range
   - start price to current price
   - change label
   - up to 3 recent point rows

Expected: the section is visibly based on trend data, not the old summary rows.

- [ ] **Step 4: Verify fluctuation row contents**

Manual check:

1. Inspect the `单价浮动` list
2. Confirm each row shows
   - species name
   - lowest price
   - highest price

Expected: the section is visibly based on fluctuation values, not recently created species.

- [ ] **Step 5: Final commit**

```bash
git add d:\Fish\src-mobile\pages\Dashboard.vue
git commit -m "feat: align mobile dashboard with pc trend view"
```
