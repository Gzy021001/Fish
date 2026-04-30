# Isolate Billing and Logs Data Spec

## Why
Currently, both the Billing (开单收银) and Logs (历史单据) pages fetch and manage the same set of bills from the backend. Modifications to bills in the Billing page directly alter the historical records shown in the Logs page, and vice versa. This causes data coupling and confusion, as the Billing page should only manage current session/active bills, while Logs should serve as a separate historical record. (Because of a previous regression, Billing still fetches the latest 10 bills from the backend).

## What Changes
- **Billing Page (`Billing.vue`)**:
  - Remove the API call to fetch historical bills (`GET /bills`) from `fetchBills`.
  - The `bills` list in `Billing.vue` will only store bills created during the current active session in memory.
  - When the page is refreshed or loaded, the list will be empty, serving strictly as a cashier/current-session view.
- **Logs Page (`Logs.vue`)**:
  - Continue to fetch all historical bills (`GET /bills?limit=0`).
  - Editing or deleting a bill here will only affect the database and the Logs view.

## Impact
- Affected specs: None.
- Affected code: `src/pages/Billing.vue`

## ADDED Requirements
### Requirement: Billing Page Isolation
The system SHALL NOT load historical bills into the Billing page. The Billing page's bill list SHALL only reflect bills created during the user's current session.

## MODIFIED Requirements
### Requirement: Billing Data Fetching
**Reason**: To ensure data isolation between active cashier sessions and historical logs.
**Migration**: Modify `fetchBills` in `Billing.vue` to do nothing (or strictly manage local state), instead of fetching from the `/bills` API.