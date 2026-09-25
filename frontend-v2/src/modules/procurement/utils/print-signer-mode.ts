/**
 * Ô ký «Trưởng phòng» trên bản in NỘI BỘ hiện ai — bao-CR-490 (đại ca chốt 25/09/2026).
 *
 *   · `approver`  — người THỰC bấm Duyệt (cột «Trưởng phòng phê duyệt» của chứng từ; phiếu cũ
 *                   chưa có cột thì backend lùi về nhật ký thao tác);
 *   · `dept_head` — trưởng phòng THEO HỒ SƠ phòng ban (`Department.manager_id` của phòng lập).
 *
 * Vì sao cần hai: người bấm Duyệt có thể là phó phòng / người được ủy quyền, còn giấy tờ nộp ra
 * ngoài lại cần đúng tên người đứng đầu phòng trên pháp lý. Mẫu thuế để trống ô ký nên không
 * đọc tới đây. Lựa chọn nhớ theo MÁY (localStorage) — người in thường in cùng một kiểu.
 */
export type PrintSignerMode = 'approver' | 'dept_head'

export const PRINT_SIGNER_MODES: ReadonlyArray<{ value: PrintSignerMode; label: string }> = [
  { value: 'approver', label: 'Ký: người duyệt' },
  { value: 'dept_head', label: 'Ký: trưởng phòng' },
]

const STORAGE_KEY = 'erp.print.signer-mode'

export function readPrintSignerMode(): PrintSignerMode {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw === 'dept_head' ? 'dept_head' : 'approver'
  } catch {
    return 'approver'
  }
}

export function savePrintSignerMode(mode: PrintSignerMode): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, mode)
  } catch {
    // Trình duyệt chặn localStorage (chế độ riêng tư) thì thôi, không phải lỗi.
  }
}

export interface HeadSignerSources {
  approver_name?: string
  approver_signature?: string
  dept_head_name?: string
  dept_head_signature?: string
}

/**
 * Tên + ảnh chữ ký cho ô «Trưởng phòng» theo chế độ. Chọn «trưởng phòng» mà phòng chưa gán
 * trưởng ở danh mục thì LÙI về người duyệt — in một ô trống trong khi có người đã duyệt thật
 * là bản in thiếu chữ ký một cách vô cớ.
 */
export function pickHeadSigner(
  mode: PrintSignerMode,
  sources: HeadSignerSources,
): { name: string; signature: string } {
  const approver = { name: sources.approver_name ?? '', signature: sources.approver_signature ?? '' }
  if (mode !== 'dept_head') return approver
  const head = { name: sources.dept_head_name ?? '', signature: sources.dept_head_signature ?? '' }
  return head.name ? head : approver
}
