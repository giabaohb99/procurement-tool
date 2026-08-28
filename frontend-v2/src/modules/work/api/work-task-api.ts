import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
import type { WorkBoard, WorkTask } from '../types/work'

/** Công việc và việc con. Xem `work-api.ts` về lý do prefix `/api/work`. */
export const workTaskApi = {
  /** Cột + task cha + mọi thứ vẽ trên thẻ, MỘT lượt gọi (D-01). */
  board: (listId: number) => apiGet<WorkBoard>(`/api/work/lists/${listId}/board`),

  get: (taskId: number) => apiGet<WorkTask>(`/api/work/tasks/${taskId}`),

  create: (values: {
    list_id: number
    title: string
    section_id?: number | null
    description?: string
    priority?: number
    start_date?: string
    due_date?: string
    sort_order?: number
    assignee_ids?: number[]
  }) => apiPost<WorkTask>('/api/work/tasks', values),

  update: (taskId: number, values: Record<string, unknown>) =>
    apiPatch<WorkTask>(`/api/work/tasks/${taskId}`, values),

  /**
   * Kéo thả kanban. Gửi MỐC TƯƠNG ĐỐI (`before_task_id`) chứ không gửi
   * `sort_order` tính sẵn — lý do đầy đủ ở `utils/kanban-drop.ts`. Máy chủ đánh
   * số lại cả cột đích nên thứ tự luôn duy nhất và không bao giờ hết khe.
   */
  move: (taskId: number, sectionId: number, beforeTaskId: number | null) =>
    apiPost<WorkTask>(`/api/work/tasks/${taskId}/move`, {
      section_id: sectionId,
      before_task_id: beforeTaskId,
    }),

  /** Xóa MỀM — vào thùng rác của list (B-09). */
  remove: (taskId: number) => apiDelete(`/api/work/tasks/${taskId}`),

  createSubtask: (taskId: number, values: { title: string }) =>
    apiPost<WorkTask>(`/api/work/tasks/${taskId}/subtasks`, values),

  /** Đặt LẠI cả bộ, không phải thêm từng người (nhiều PIC được — Q5). */
  setAssignees: (taskId: number, picIds: number[], followerIds: number[] = []) =>
    apiPut<WorkTask>(`/api/work/tasks/${taskId}/assignees`, {
      pic_ids: picIds,
      follower_ids: followerIds,
    }),

  setTags: (taskId: number, tagIds: number[]) =>
    apiPut<WorkTask>(`/api/work/tasks/${taskId}/tags`, { tag_ids: tagIds }),

  /** `optionId = null` là bỏ chọn giá trị của trường nhãn đó (B-08). */
  setLabel: (taskId: number, fieldId: number, optionId: number | null) =>
    apiPut<WorkTask>(`/api/work/tasks/${taskId}/label`, {
      field_id: fieldId,
      option_id: optionId,
    }),
}
