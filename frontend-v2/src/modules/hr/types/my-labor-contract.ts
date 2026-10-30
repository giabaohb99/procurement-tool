/**
 * "Hợp đồng của tôi" (duoc-CR-652) — khớp `MyLaborContractOut` của backend (`/api/me/labor-contracts`).
 * Hình dạng RÚT GỌN so với `LaborContract` của HR: không cờ `can_*`, không `transitions`, không id tệp.
 */
export interface MyLaborContract {
  id: number
  code: string
  contract_no: string
  company_name: string
  contract_type: number
  /** Trạng thái LƯU (2 Đã ký / 4 Đã chấm dứt). */
  status: number
  /** Trạng thái hiển thị — thêm "Hết hạn" (3) suy ra theo ngày. */
  effective_status: number
  sign_date: string | null
  start_date: string
  end_date: string | null
  terminated_date: string | null
  job_title: string
  base_salary: number
  has_generated_file: boolean
  has_signed_file: boolean
}

export interface MyLaborContractListResult {
  items: MyLaborContract[]
}
