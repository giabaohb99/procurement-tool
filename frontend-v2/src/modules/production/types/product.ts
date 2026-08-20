export interface Product {
  id: number
  code: string
  name: string
  invoice_name?: string
  legal_name?: string
  item_group?: string
  unit?: string
  hh_code?: string
  hh_name?: string
  specs?: string
  is_active: boolean
  thumbnail_url?: string
  created_at?: string
  updated_at?: string
}
