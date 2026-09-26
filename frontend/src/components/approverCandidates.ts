// bao-CR-499 — danh sách chọn ô «Trưởng phòng phê duyệt» của bản v1: chỉ người DUYỆT ĐƯỢC chứng
// từ đó (backend `core/approver_candidates.py`), cùng nguồn với bản v2 — không lấy cả danh mục
// nhân sự nữa (đại ca chốt hướng 1, 26/09/2026).
import { api } from '../api/client'

export async function loadApproverCandidates(apiBase: string, id: number, doc: any): Promise<any[]> {
  try {
    const r = id > 0
      ? await api.get(`${apiBase}/${id}/approver-candidates`, { _silent: true } as any)
      : await api.get(`${apiBase}/meta/approver-candidates`, {
          params: {
            department: doc.department || '', department_id: Number(doc.department_id) || 0,
            company_id: Number(doc.company_id) || 0, handler_dept_id: Number(doc.handler_dept_id) || 0,
          },
          _silent: true,
        } as any)
    return r.data.data.items || []
  } catch {
    return []
  }
}
