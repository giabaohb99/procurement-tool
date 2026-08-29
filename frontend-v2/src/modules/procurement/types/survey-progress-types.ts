export interface SurveyProgressItem {
  stt?: number
  sr_id: number
  code: string
  company_id: number
  company: string
  department_id: number
  department: string
  requester: string
  purpose: string
  request_date: string
  status: string
  internal_line_code?: string
  item_group: string
  requirement_detail: string
  other_requirement?: string
  request_qty: number
  uom: string
  proposed_price?: number
  assignee?: string
  assignee_name?: string
  received_date: string
  result_due_date: string
  result_date: string
  days_late: number | null
  handling_days: number | null
  progress_state: string
  line_status: string
  option_count: number

  opt_label?: string
  opt_supplier_code?: string
  opt_supplier_name?: string
  opt_internal_code?: string
  opt_product_code?: string
  opt_product_name?: string
  opt_spec?: string
  opt_origin?: string
  opt_quote_unit?: string
  opt_moq?: number
  opt_price?: number
  opt_volume_range?: string
  opt_vat?: number
  opt_delivery_time?: string
  opt_delivery_place?: string
  opt_shipping_cost?: number
  opt_sample_ready?: boolean
  opt_lab_result?: string
  opt_note?: string
}

export interface SurveyProgressResult {
  items: SurveyProgressItem[]
  total: number
  show_supplier: boolean
  states?: string[]
}
