import { describe, expect, it, vi } from 'vitest'

import { makeLaborContract } from '../components/labor-contract-fixture'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import type { LaborContract } from '../types/labor-contract'
import { sortRowsByCell } from '@/shared/utils/sort-rows-by-cell'
import {
  buildEmployeeLaborContractColumns,
  EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS,
} from './employee-labor-contract-columns'
import {
  buildEmployeeWorkHistoryColumns,
  EMPLOYEE_WORK_HISTORY_SORT_GETTERS,
} from './employee-work-history-columns'
import {
  buildEmployeeWorkHistoryDecisionColumns,
  EMPLOYEE_WORK_HISTORY_DECISION_SORT_GETTERS,
} from './employee-work-history-decision-columns'

//  duoc-CR-748 — ba bảng ở tab hồ sơ nhân sự (Hợp đồng · Quá trình công tác · Quyết định bổ nhiệm) nạp đủ dòng và
//  xếp ở trình duyệt bằng `sortRowsByCell`. Cột bật `sortable` mà thiếu bộ lấy giá trị là "bấm không ăn" — im lặng,
//  không lỗi nào hiện ra; bài dưới canh điều đó cho cả ba bảng.

function workRow(overrides: Partial<EmployeeWorkHistory> & { id: number }): EmployeeWorkHistory {
  return {
    employee_id: 1,
    event_type: 3,
    from_date: '2026-01-01',
    to_date: null,
    company_id: 10,
    company_name: 'DEGO',
    department_id: 20,
    department_name: 'Phòng KD',
    position_id: 30,
    position_label: 'Trưởng phòng',
    decision_no: '',
    decision_date: null,
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: false,
    can_apply: false,
    ...overrides,
  }
}

function contract(overrides: Partial<LaborContract> & { id: number }): LaborContract {
  return makeLaborContract({ code: `HDLD-${overrides.id}`, ...overrides })
}

const ids = (rows: { id: number }[]) => rows.map((r) => r.id)

describe('sortable columns always have a sort getter', () => {
  it('Hợp đồng: every sortable column is understood, salary included', () => {
    const columns = buildEmployeeLaborContractColumns({
      isBusy: () => false,
      canReadSigned: true,
      onEdit: vi.fn(),
      onGenerate: vi.fn(),
      onDownloadDocument: vi.fn(),
      onUploadSigned: vi.fn(),
      onDownloadSigned: vi.fn(),
      onTransition: vi.fn(),
      onDelete: vi.fn(),
    })
    const sortable = columns.filter((c) => c.sortable).map((c) => c.key)
    expect(sortable).toEqual(['contract_no', 'status', 'contract_type', 'period', 'job_title', 'base_salary'])
    for (const key of sortable) expect(EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS[key], key).toBeTypeOf('function')
    //  Tệp và Thao tác không có giá trị để xếp.
    expect(columns.find((c) => c.key === 'actions')?.sortable).toBeFalsy()
  })

  it('Quá trình công tác: every data column sorts, the action column does not', () => {
    const columns = buildEmployeeWorkHistoryColumns({
      canOpenFiles: false,
      onOpenFiles: vi.fn(),
      actions: {
        onEdit: vi.fn(),
        onApply: vi.fn(),
        onDelete: vi.fn(),
        isApplying: () => false,
        isDeleting: () => false,
      },
    })
    for (const column of columns) {
      const hasGetter = typeof EMPLOYEE_WORK_HISTORY_SORT_GETTERS[column.key] === 'function'
      expect(Boolean(column.sortable), column.key).toBe(hasGetter)
    }
    expect(columns.find((c) => c.key === 'actions')?.sortable).toBeFalsy()
  })

  it('Quyết định bổ nhiệm: every column sorts, the summary included', () => {
    const columns = buildEmployeeWorkHistoryDecisionColumns({ canOpenFiles: true, onOpenFiles: vi.fn() })
    for (const column of columns) {
      expect(column.sortable, column.key).toBe(true)
      expect(EMPLOYEE_WORK_HISTORY_DECISION_SORT_GETTERS[column.key], column.key).toBeTypeOf('function')
    }
  })
})

describe('EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS', () => {
  const rows = [
    contract({ id: 1, effective_status: 5, contract_type: 9, base_salary: 0, contract_no: '' }),
    contract({ id: 2, effective_status: 1, contract_type: 1, base_salary: 15_000_000, contract_no: 'Ánh-02' }),
    contract({ id: 3, effective_status: 3, contract_type: 3, base_salary: 9_500_000, contract_no: 'An-03' }),
  ]

  it('sorts status by lifecycle (Nháp → Hết hạn → Đã hủy), not by the label alphabet', () => {
    //  Theo chữ cái thì "Đã hủy" đứng trước "Hết hạn" và "Nháp" — đúng lỗi luật §8 cấm.
    expect(ids(sortRowsByCell(rows, 'status', 'asc', EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS))).toEqual([2, 3, 1])
    expect(ids(sortRowsByCell(rows, 'status', 'desc', EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS))).toEqual([1, 3, 2])
  })

  it('sorts contract type in the code-set order (Thử việc first, Khác last)', () => {
    expect(ids(sortRowsByCell(rows, 'contract_type', 'asc', EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS))).toEqual([2, 3, 1])
  })

  it('sorts salary as a number, with 0 being a real value (a contract may carry no salary yet)', () => {
    expect(ids(sortRowsByCell(rows, 'base_salary', 'desc', EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS))).toEqual([2, 3, 1])
    expect(ids(sortRowsByCell(rows, 'base_salary', 'asc', EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS))).toEqual([1, 3, 2])
  })

  it('sorts the contract number by the text shown, falling back to the system code when no number was typed', () => {
    //  Dòng 1 không có số HĐ nên ô hiện mã "HDLD-1" — xếp đúng chữ đó, có dấu tiếng Việt.
    expect(ids(sortRowsByCell(rows, 'contract_no', 'asc', EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS))).toEqual([3, 2, 1])
  })
})

describe('EMPLOYEE_WORK_HISTORY_SORT_GETTERS', () => {
  it('puts open-ended rows (no end date) at the END in both directions', () => {
    const rows = [
      workRow({ id: 1, to_date: null, is_current: true }),
      workRow({ id: 2, to_date: '2025-06-30' }),
      workRow({ id: 3, to_date: '2026-03-31' }),
    ]
    expect(ids(sortRowsByCell(rows, 'to_date', 'asc', EMPLOYEE_WORK_HISTORY_SORT_GETTERS))).toEqual([2, 3, 1])
    expect(ids(sortRowsByCell(rows, 'to_date', 'desc', EMPLOYEE_WORK_HISTORY_SORT_GETTERS))).toEqual([3, 2, 1])
  })

  it('sorts event type by the code-set order and Vietnamese names with diacritics', () => {
    const rows = [
      workRow({ id: 1, event_type: 9, department_name: 'Đào tạo' }),
      workRow({ id: 2, event_type: 1, department_name: 'Ban giám đốc' }),
      workRow({ id: 3, event_type: 3, department_name: '' }),
    ]
    expect(ids(sortRowsByCell(rows, 'event_type', 'asc', EMPLOYEE_WORK_HISTORY_SORT_GETTERS))).toEqual([2, 3, 1])
    //  Phòng ban trống ("—") xuống cuối cả hai chiều; "Đ" đứng sau "B".
    expect(ids(sortRowsByCell(rows, 'department_name', 'asc', EMPLOYEE_WORK_HISTORY_SORT_GETTERS))).toEqual([2, 1, 3])
    expect(ids(sortRowsByCell(rows, 'department_name', 'desc', EMPLOYEE_WORK_HISTORY_SORT_GETTERS))).toEqual([1, 2, 3])
  })

  it('treats "no file" (shown as a dash) as blank in the file column', () => {
    const rows = [workRow({ id: 1, file_count: 0 }), workRow({ id: 2, file_count: 3 }), workRow({ id: 3, file_count: 1 })]
    expect(ids(sortRowsByCell(rows, 'files', 'asc', EMPLOYEE_WORK_HISTORY_SORT_GETTERS))).toEqual([3, 2, 1])
    expect(ids(sortRowsByCell(rows, 'files', 'desc', EMPLOYEE_WORK_HISTORY_SORT_GETTERS))).toEqual([2, 3, 1])
  })

  it('sorts the decision summary by the line the cell shows', () => {
    const rows = [
      workRow({ id: 1, department_name: 'Phòng KD', position_label: 'Trưởng phòng', company_name: 'DEGO' }),
      workRow({ id: 2, department_name: 'Kế toán', position_label: '', company_name: 'DEGO' }),
      workRow({ id: 3, department_name: '', position_label: '', company_name: '' }),
    ]
    expect(ids(sortRowsByCell(rows, 'summary', 'asc', EMPLOYEE_WORK_HISTORY_DECISION_SORT_GETTERS))).toEqual([2, 1, 3])
  })
})
