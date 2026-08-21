/**
 * MÃ ĐƯA VÀO SỐ HIỆU — bốn thẻ của mẫu số hiệu lấy mã từ bốn chỗ khác nhau.
 *
 * `08/2026/TB-NSHC-DEGO` = `{STT}/{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}`, mà mã
 * của từng phần vốn nằm ở bốn màn thuộc ba phân hệ. Nhóm này gom chúng lại để
 * sửa ngay tại trang Quy tắc đánh số — xem `issue_code_service.py`.
 */

export const ISSUE_CODE_KIND = {
  company: 'company',
  department: 'department',
  /** Mã riêng của một phòng TẠI một pháp nhân (`issue_code_override`). */
  departmentCompany: 'department_company',
  docType: 'doc_type',
  book: 'book',
} as const

export type IssueCodeKind = (typeof ISSUE_CODE_KIND)[keyof typeof ISSUE_CODE_KIND]

export interface IssueCodeRow {
  kind: IssueCodeKind
  id: number
  /** Chỉ có ở `department_company` — pháp nhân của mã riêng. */
  company_id?: number
  name: string
  /** Mã hiển thị của bản ghi (khác mã đi vào số hiệu); với mã riêng là tên pháp nhân. */
  code: string
  issue_code: string
  /**
   * Đơn vị này đã có văn bản mang số chưa. Đổi mã sau đó thì số cũ giữ nguyên
   * chuỗi còn số mới dùng mã mới — sổ sẽ có hai kiểu mã cạnh nhau.
   */
  da_cap_so: boolean
  /**
   * Chỉ có ở phòng ban: `false` = đơn vị kinh doanh / ban dự án, mã của nó
   * **không xuất hiện trong số hiệu** (A05) nên sửa cũng không ra tới đâu.
   */
  trong_so_hieu?: boolean
}

export interface IssueCodeGroups {
  companies: IssueCodeRow[]
  departments: IssueCodeRow[]
  department_companies: IssueCodeRow[]
  doc_types: IssueCodeRow[]
  books: IssueCodeRow[]
}

export interface IssueCodeUpdateInput {
  kind: IssueCodeKind
  id: number
  company_id?: number
  issue_code: string
  /** Người dùng đã đọc cảnh báo «đã cấp số» và vẫn muốn đổi. */
  force?: boolean
}
