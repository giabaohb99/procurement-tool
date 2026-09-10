/**
 * Kiểu dữ liệu phân hệ Điểm cà phê — khớp serializer của
 * `backend/app/modules/coffee_point/service.py`. Trạng thái/loại là SỐ (IntEnum
 * theo luật R2), nhãn tiếng Việt backend trả kèm (`*_label`) hoặc lấy từ
 * `GET /api/coffee/meta` — KHÔNG gõ lại nhãn ở TypeScript.
 */

export interface CoffeeMetaOption {
  value: number
  label: string
}

export interface CoffeeMeta {
  levels: CoffeeMetaOption[]
  ledger_types: CoffeeMetaOption[]
  member_statuses: CoffeeMetaOption[]
  match_statuses: CoffeeMetaOption[]
  sync_kinds: CoffeeMetaOption[]
}

export interface CoffeePolicy {
  id: number
  company_id: number
  level_code: number
  level_label: string
  monthly_points: number
  effective_from: string
  note: string
  /** Dòng đã được kỳ cấp phát dùng tới — backend chặn sửa, UI ẩn nút. */
  locked: boolean
}

export interface MenuItem {
  product_id: number
  code: string
  name: string
  price: number
  category: string
  image: string
}

export interface SelfOrderResult {
  code: string
  pos_order_id: number
  total: number
  /** null = cấp vô hạn, không hiển thị số dư. */
  balance: number | null
}

/** Một dòng bảng DỰ KIẾN cấp phát kỳ (A-06 — từng kỳ phải có người chốt). */
export interface ResetPreviewRow {
  employee_id: number
  employee_code: string
  employee_name: string
  level_code: number
  level_label: string
  current_balance: number
  expire: number
  grant: number
  already_granted: boolean
}

export interface ResetPreview {
  period: string
  preview: ResetPreviewRow[]
  no_policy: number[]
}

export interface CoffeeMember {
  id: number
  employee_id: number
  employee_code: string
  employee_name: string
  department_name: string
  company_id: number
  level_code: number
  level_label: string
  status: number
  status_label: string
  pos_partner_id: number
  pos_partner_code: string
  matched_at: string
  /** Cấp VÔ HẠN (Chúa tể HĐQT): không cấp/không chặn, ví hiện "Không giới hạn". */
  unlimited: boolean
  balance: number | null
}

export interface CoffeeLedgerRow {
  id: number
  employee_id: number
  employee_code: string
  employee_name: string
  period: string
  type: number
  type_label: string
  points: number
  reason: string
  pos_order_id: number
  pos_code: string
  created_at: string
  created_by: number
}

export interface CoffeeWallet {
  member: CoffeeMember | null
  balance: number
  granted: number
  spent: number
  period?: string
  items: CoffeeLedgerRow[]
}

export interface PosOrderRow {
  id: number
  pos_order_id: number
  pos_code: string
  purchase_date: string
  pos_partner_id: number
  employee_id: number
  employee_name: string
  total: number
  points_paid: number
  match_status: number
  match_status_label: string
  is_voided: number
  resolve_note: string
  synced_at: string
}

export interface PosSyncRun {
  id: number
  kind: number
  kind_label: string
  status: number
  status_label: string
  started_at: string
  finished_at: string
  cursor_from: string
  cursor_to: string
  fetched: number
  written: number
  skipped: number
  error: string
  detail: string
  created_by: number
}

export interface PosPartnerHit {
  pos_partner_id: number
  code: string
  name: string
  phone: string
  point: number
}

export interface CounterLookupResult {
  found: boolean
  name?: string
  balance?: number
  unlimited?: boolean
}

/** Màn Quản lý POS — số đọc TRỰC TIẾP từ POS365 lúc mở màn (chỉ-đọc, doc 09 §12). */
export interface PosDashboard {
  store_url: string
  today: {
    orders: number
    revenue: number
    cash: number
    account: number
    points: number
    voided: number
  }
  by_day: { label: string; value: number }[]
  recent: {
    pos_order_id: number
    code: string
    time: string
    total: number
    method: string
    is_points: boolean
    is_voided: boolean
    partner_name: string
  }[]
}
