export type ItemGroup = {
  id: number
  code?: string
  name: string
  std_days?: string | number | null
  std_days_unavail?: string | number | null
  apply_date?: string | null
  note?: string | null
  is_active: boolean
  created_at?: string
  updated_at?: string
}
