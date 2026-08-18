import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
import type {
  ApprovalFlow,
  ApprovalInstance,
  ApprovalNode,
  ApprovalOptions,
  ApprovalSwitch,
  ApprovalTask,
  ApprovalTrail,
  Delegation,
  MyTask,
} from '../types/approval'

const FLOW_URL = '/api/approval-flows'
const INSTANCE_URL = '/api/approvals'
const DELEGATION_URL = '/api/delegations'

interface Paged<T> {
  total: number
  items: T[]
}

export const approvalFlowApi = {
  options: () => apiGet<ApprovalOptions>(`${FLOW_URL}/options`),
  list: (entity?: string) =>
    apiGet<Paged<ApprovalFlow>>(FLOW_URL, { params: entity ? { entity } : undefined }),
  getById: (id: number) => apiGet<ApprovalFlow>(`${FLOW_URL}/${id}`),
  create: (values: Partial<ApprovalFlow>) => apiPost<ApprovalFlow>(FLOW_URL, values),
  update: (id: number, values: Partial<ApprovalFlow>) =>
    apiPatch<ApprovalFlow>(`${FLOW_URL}/${id}`, values),
  remove: (id: number) => apiDelete<null>(`${FLOW_URL}/${id}`),

  /**
   * Thêm một bước. `asBranch` = nhánh song song của chặng đó; mặc định là chèn
   * hẳn một CHẶNG MỚI tại `seq` và backend tự đẩy các chặng sau xuống.
   */
  addNode: (flowId: number, values: Partial<ApprovalNode>, asBranch = false) =>
    apiPost<ApprovalNode>(`${FLOW_URL}/${flowId}/nodes`, values, {
      params: { as_branch: asBranch },
    }),
  updateNode: (flowId: number, nodeId: number, values: Partial<ApprovalNode>) =>
    apiPatch<ApprovalNode>(`${FLOW_URL}/${flowId}/nodes/${nodeId}`, values),
  removeNode: (flowId: number, nodeId: number) =>
    apiDelete<null>(`${FLOW_URL}/${flowId}/nodes/${nodeId}`),
  /** Thứ tự sau khi kéo thả. Mỗi phần tử là một CHẶNG, chứa id các nhánh của nó. */
  reorderNodes: (flowId: number, stages: number[][]) =>
    apiPut<ApprovalFlow>(`${FLOW_URL}/${flowId}/nodes/reorder`, { stages }),

  switches: () => apiGet<ApprovalSwitch[]>(`${FLOW_URL}/switches`),
  /** I26 — đường lui của cả phase: tắt là quay về đường duyệt cũ ngay. */
  setSwitch: (values: ApprovalSwitch) => apiPut<ApprovalSwitch>(`${FLOW_URL}/switches`, values),
}

export const approvalApi = {
  /** I17 — mọi thứ đang chờ tôi, của cả văn thư lẫn thu mua. */
  myTasks: (entity?: string) =>
    apiGet<Paged<MyTask>>(`${INSTANCE_URL}/my-tasks`, { params: entity ? { entity } : undefined }),

  getById: (id: number) => apiGet<ApprovalInstance>(`${INSTANCE_URL}/${id}`),
  trail: (id: number) => apiGet<ApprovalTrail>(`${INSTANCE_URL}/${id}/trail`),

  approve: (id: number, comment: string, subject: Record<string, unknown> = {}) =>
    apiPost<ApprovalInstance>(`${INSTANCE_URL}/${id}/approve`, { comment, subject }),
  reject: (id: number, reason: string) =>
    apiPost<ApprovalInstance>(`${INSTANCE_URL}/${id}/reject`, { reason }),
  return: (id: number, reason: string, toSeq?: number | null,
           subject: Record<string, unknown> = {}) =>
    apiPost<ApprovalInstance>(`${INSTANCE_URL}/${id}/return`, {
      reason,
      to_seq: toSeq ?? null,
      subject,
    }),
  withdraw: (id: number, reason: string) =>
    apiPost<ApprovalInstance>(`${INSTANCE_URL}/${id}/withdraw`, { reason }),
  comment: (id: number, comment: string) =>
    apiPost<null>(`${INSTANCE_URL}/${id}/comment`, { comment }),

  reassign: (taskId: number, toEmployeeId: number, reason: string) =>
    apiPatch<ApprovalTask>(`${INSTANCE_URL}/tasks/${taskId}/reassign`, {
      to_employee_id: toEmployeeId,
      reason,
    }),
  /** I23 — nghỉ việc: chuyển hết việc đang chờ sang người khác một lần. */
  handover: (fromEmployeeId: number, toEmployeeId: number, reason: string) =>
    apiPost<{ count: number }>(`${INSTANCE_URL}/handover`, {
      from_employee_id: fromEmployeeId,
      to_employee_id: toEmployeeId,
      reason,
    }),
}

export const delegationApi = {
  list: (employeeId?: number) =>
    apiGet<Paged<Delegation>>(DELEGATION_URL, {
      params: employeeId ? { employee_id: employeeId } : undefined,
    }),
  create: (values: Partial<Delegation>) => apiPost<Delegation>(DELEGATION_URL, values),
  update: (id: number, values: Partial<Delegation>) =>
    apiPatch<Delegation>(`${DELEGATION_URL}/${id}`, values),
  /** Ngưng chứ không xóa: dấu vết duyệt trỏ vào id này. */
  stop: (id: number) => apiDelete<null>(`${DELEGATION_URL}/${id}`),
}
