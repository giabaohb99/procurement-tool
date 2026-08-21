import { companyApi } from '@/modules/hr/api/company-api'
import { departmentApi } from '@/modules/hr/api/department-api'
import { employeeApi } from '@/modules/hr/api/employee-api'
import type { FilterFieldDefinition, SelectOption } from '@/shared/conditional-filter'
import { docTypeApi } from '../api/doc-catalog-api'
import { documentBookApi } from '../api/document-book-api'
import { STATUS_LABELS } from '../types/document-record'
import { CONFIDENTIAL_LEVELS, URGENCY_LEVELS } from '../types/security-level'

/**
 * Trường của BỘ LỌC NÂNG CAO trên danh sách VĂN BẢN.
 *
 * Lọc do SERVER làm (khác màn "Áp dụng cho tôi" lọc tại trình duyệt): danh sách
 * này sẽ lên hàng chục nghìn dòng, và nạp hết về client còn có nghĩa là gửi cho
 * máy người dùng cả những văn bản họ không được xem.
 *
 * ⚠️ Mọi `name` ở đây PHẢI nằm trong `FILTERABLE` của
 * `backend/app/modules/document/controller.py`. Thiếu một tên là bộ lọc vẫn
 * chạy, vẫn hiện chip điều kiện, nhưng backend **lặng lẽ bỏ qua** — danh sách
 * không đổi và không ai hiểu vì sao.
 *
 * Ô tham chiếu (loại, pháp nhân, phòng, người, sổ) gửi đi **ID** chứ không gửi
 * tên: lọc theo tên thì đổi tên phòng là bộ lọc cũ trượt sạch, và `contains`
 * còn khớp cả chuỗi con (lọc "Hân" ra luôn "Ngọc Hân").
 */

const PAGE_SIZE = 50

async function docTypeOptions(search: string): Promise<SelectOption[]> {
  const res = await docTypeApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: `${item.code} · ${item.name}` }))
}

async function companyOptions(search: string): Promise<SelectOption[]> {
  const res = await companyApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

async function departmentOptions(search: string): Promise<SelectOption[]> {
  const res = await departmentApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

/** Kèm MÃ vào nhãn — danh mục nhân sự có người trùng tên, thiếu mã thì chọn nhầm. */
async function employeeOptions(search: string): Promise<SelectOption[]> {
  const res = await employeeApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({
    value: String(item.id),
    label: `${item.full_name}${item.code ? ` · ${item.code}` : ''}`,
  }))
}

async function bookOptions(search: string): Promise<SelectOption[]> {
  const res = await documentBookApi.list({ q: search, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

export const DOCUMENT_LIST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'title', label: 'Trích yếu', type: 'text' },
  //  Ba kiểu số cùng tồn tại: mã bất biến (DEGO-QC-001), số theo sổ
  //  (01/2026/CV-DEGO) và SỐ CŨ của bản giấy — người dùng lâu năm tra theo số
  //  họ đã thuộc, nên phải lọc được cả ba.
  { name: 'doc_code', label: 'Mã tài liệu', type: 'text' },
  { name: 'issue_number', label: 'Số hiệu theo sổ', type: 'text' },
  { name: 'legacy_code', label: 'Số hiệu cũ (bản giấy)', type: 'text' },
  //  Lọc theo NGĂN TỦ: "cho tôi mọi văn bản đang nằm ở Tủ A2" là câu hỏi lúc đi
  //  lấy hồ sơ giấy, và cũng là lúc kiểm kê kho.
  { name: 'storage_location', label: 'Nơi lưu trữ cứng', type: 'text' },
  { name: 'keywords', label: 'Từ khóa', type: 'text' },

  { name: 'doc_type_id', label: 'Loại văn bản', type: 'select', fetchOptions: docTypeOptions },
  {
    name: 'company_id',
    label: 'Pháp nhân ban hành',
    type: 'select',
    fetchOptions: companyOptions,
  },
  { name: 'department_id', label: 'Phòng chủ trì', type: 'select', fetchOptions: departmentOptions },
  {
    name: 'owner_employee_id',
    label: 'Người chịu trách nhiệm',
    type: 'select',
    fetchOptions: employeeOptions,
  },
  { name: 'book_id', label: 'Sổ văn bản', type: 'select', fetchOptions: bookOptions },

  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    options: Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label })),
  },
  {
    name: 'secrecy_level',
    label: 'Mức mật',
    type: 'select',
    options: CONFIDENTIAL_LEVELS.map((item) => ({ value: String(item.id), label: item.name })),
  },
  {
    name: 'urgency',
    label: 'Độ khẩn',
    type: 'select',
    options: URGENCY_LEVELS.map((item) => ({ value: String(item.id), label: item.name })),
  },

  { name: 'effective_date', label: 'Ngày hiệu lực', type: 'date' },
  { name: 'expire_date', label: 'Ngày hết hiệu lực', type: 'date' },
  { name: 'issue_year', label: 'Năm ban hành', type: 'number' },
  //  Cờ do hệ bật khi văn bản cha đổi (J10) — lọc ra để rà cho hết.
  { name: 'needs_review', label: 'Cần rà soát lại', type: 'boolean', operators: ['is'] },
]
