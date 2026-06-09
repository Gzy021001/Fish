# Mobile Dashboard Trend Design

## Goal

Replace the mobile dashboard sections `价格摘要` and `最近录入品种` with mobile-friendly versions of the PC dashboard's `周单价趋势` and `单价浮动`.

## Scope

In scope:

- Update the first dashboard detail section to show weekly price trend cards.
- Update the second dashboard detail section to show price fluctuation rows.
- Reuse existing mobile dashboard API calls and local computed data.
- Keep the implementation isolated to `src-mobile/pages/Dashboard.vue`.

Out of scope:

- Backend API changes.
- PC dashboard changes.
- New filters, tabs, or date pickers on mobile dashboard.
- Full PC-style long scrolling detail cards on mobile.

## Chosen Approach

Use the current mobile dashboard data fetch flow, but replace the two existing derived lists with two new mobile-specific derived views:

- `周单价趋势`: compact trend cards based on the same trend points used by PC.
- `单价浮动`: compact fluctuation list showing min and max price per species.

This keeps the data logic aligned with PC while keeping the mobile page short enough to scan.

## Data Sources

Keep the existing calls:

- `GET /api/species?include_images=false`
- `GET /api/stats/price-trend-batch?species_ids=...`

No new request is needed.

## Weekly Price Trend Section

Replace the current `价格摘要` section with `周单价趋势`.

Each card shows:

- species name
- start date and end date
- start price to current price
- total price change
- last 3 date points with their corresponding prices and point-to-point change

Rules:

- Ignore species with no trend points.
- Reuse the PC-side packaging item filtering rule.
- Sort by absolute total change descending.
- Keep the top 6 items.

## Price Fluctuation Section

Replace the current `最近录入品种` section with `单价浮动`.

Each row shows:

- species name
- min price
- max price

Rules:

- Compute min and max from all trend points of that species.
- Ignore species with no trend points.
- Reuse the PC-side packaging item filtering rule.
- Sort by `(maxPrice - minPrice)` descending.
- Keep the top 6 items.

## Mobile Presentation

`周单价趋势` should stay card-based, but more compressed than PC:

- one column
- no inner long scroll area
- at most 3 detail rows per card

`单价浮动` should be a short compact list:

- one row per species
- no extra metadata from the old `最近录入品种` block

## Empty States

Use section-specific empty states:

- `暂无周单价趋势数据`
- `暂无单价浮动数据`

## Verification

Success criteria:

1. Mobile dashboard no longer shows `价格摘要` and `最近录入品种`.
2. Mobile dashboard shows `周单价趋势` and `单价浮动`.
3. Trend cards and fluctuation rows use the same trend dataset already loaded by the page.
4. Packaging items are excluded consistently with PC logic.
5. Only `src-mobile/pages/Dashboard.vue` is modified for this feature.
