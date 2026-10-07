import type { EmployeeDetail } from '../types/employee'
import type { LaborContract } from '../types/labor-contract'

/** Hợp đồng NHÁP tối thiểu cho test; ghi đè từng trường theo ca. */
export function makeLaborContract(overrides: Partial<LaborContract> = {}): LaborContract {
  return {
    id: 1,
    code: 'HDLD-0001',
    contract_no: '01/2026/HDLD',
    employee_id: 7,
    company_id: 10,
    company_name: 'Công ty A',
    department_id: 20,
    department_name: 'Phòng Nhân sự',
    template_id: 0,
    template_name: '',
    contract_type: 2,
    status: 1,
    effective_status: 1,
    sign_date: null,
    start_date: '2026-01-01',
    end_date: '2026-12-31',
    job_title: 'Chuyên viên',
    work_location: 'Hà Nội',
    base_salary: 15_000_000,
    insurance_salary: 10_000_000,
    allowance: 500_000,
    allowance_note: 'Ăn trưa',
    note: '',
    has_generated_file: false,
    generated_at: null,
    has_signed_file: false,
    terminated_date: null,
    terminate_reason: '',
    created_at: '2026-01-01T00:00:00',
    created_by_name: 'HR',
    can_edit: true,
    can_delete: true,
    can_generate: true,
    can_print: false,
    can_upload_signed: true,
    transitions: [2, 5],
    ...overrides,
  }
}

export const laborContractEmployee = {
  id: 7,
  code: 'NSU007',
  full_name: 'Nguyễn Văn B',
  company_id: 10,
  company_name: 'Công ty A',
  department_id: 20,
  position: 'Chuyên viên',
  work_location: 'Hà Nội',
} as unknown as EmployeeDetail
