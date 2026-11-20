// bao-CR-499 — danh sách chọn ô "Trưởng phòng phê duyệt" của bản v1: chỉ người DUYỆT ĐƯỢC chứng
// từ đó (backend `core/approver_candidates.py`), cùng nguồn với bản v2 — không lấy cả danh mục
// nhân sự nữa (đại ca chốt hướng 1, 26/09/2026).
import { api } from '../api/client'

export async function loadApproverCandidates(apiBase: string, id: number, doc: any): Promise<any[]> {
  return (await loadApproverCandidatesWithDefault(apiBase, id, doc)).items
}

/** bao-CR-786: kèm `defaultId` — ĐMH đang lập trả trưởng phòng của phòng trên form để điền sẵn đơn tạo thẳng. */
export async function loadApproverCandidatesWithDefault(apiBase: string, id: number, doc: any): Promise<{ items: any[]; defaultId: number; defaults: any }> {
  try {
    const r = id > 0
      ? await api.get(`${apiBase}/${id}/approver-candidates`, { _silent: true } as any)
      : await api.get(`${apiBase}/meta/approver-candidates`, {
          params: {
            department: doc.department || '', department_id: Number(doc.department_id) || 0,
            company_id: Number(doc.company_id) || 0, handler_dept_id: Number(doc.handler_dept_id) || 0,
            // bao-CR-552: backend luôn đưa Trưởng bộ phận đang chọn vào danh sách.
            head_of_dept_id: Number(doc.head_of_dept_id) || 0,
          },
          _silent: true,
        } as any)
    // bao-CR-787: `defaults` = công ty / phòng xử lý mặc định của đơn tạo thẳng (chỉ ĐMH đang lập trả).
    return { items: r.data.data.items || [], defaultId: Number(r.data.data.default_employee_id) || 0, defaults: r.data.data }
  } catch {
    return { items: [], defaultId: 0, defaults: {} }
  }
}
