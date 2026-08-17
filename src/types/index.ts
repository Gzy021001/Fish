// ============================================================
//  后端 Pydantic Schema → 前端 DTO 类型映射
//  由 backend/schemas.py 推导，保持字段名一致
// ============================================================

/* ---------- 品种 ---------- */
export interface Species {
  id: number
  name_zh: string
  default_unit: string
  default_price: number
  image_url: string | null
  supplier_name: string | null
  supplier_note: string | null
  release_date: string | null
  created_at: string | null
}

/* ---------- 单据 ---------- */
export interface SpeciesInBill {
  id: number
  name_zh: string
  default_unit: string
  release_date: string | null
}

export interface Bill {
  id: number
  species_id: number
  user_id: number
  weight: number
  unit_price: number
  currency: string
  fee_type: string
  fee_value: number
  status: string
  release_date: string | null
  created_at: string
  subtotal: number
  total_amount: number
  species: SpeciesInBill | null
}

/* ---------- 审计日志 ---------- */
export interface AuditLog {
  id: number
  bill_id: number | null
  species_id: number | null
  entity_type: string
  action: string
  old_data: string | null
  new_data: string | null
  user_id: number
  created_at: string
}

/* ---------- 批量导入 ---------- */
export interface BatchImportRow {
  name_zh: string
  weight: number
  unit_price: number
  fee_value: number
  release_date?: string
}

export interface BatchImportResult {
  success_count: number
  skip_count: number
  errors: string[]
}

/* ---------- HTTP 通用 ---------- */
export interface ApiError {
  response?: {
    status: number
    data?: {
      detail?: string
      error?: string
    }
  }
  config?: Record<string, unknown>
  code?: string
  message?: string
}
