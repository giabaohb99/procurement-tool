import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
import type { WorkBoard, WorkTask, WorkTaskLink } from '../types/work'

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
    /** `WORK_TASK_KIND.MILESTONE` để tạo thẳng một cột mốc (B-14). */
    kind?: number
    assignee_ids?: number[]
  }) => apiPost<WorkTask>('/api/work/tasks', values),

  update: (taskId: number, values: Record<string, unknown>) =>
    apiPatch<WorkTask>(`/api/work/tasks/${taskId}`, values),

  /**
   * Kéo thả. Gửi MỐC TƯƠNG ĐỐI (`before_task_id`) chứ không gửi `sort_order`
   * tính sẵn — lý do đầy đủ ở `utils/kanban-drop.ts`. Máy chủ đánh số lại cả
   * hàng đích nên thứ tự luôn duy nhất và không bao giờ hết khe.
   *
   * `sectionId` null = xếp lại một VIỆC CON trong cụm của cha nó; việc con
   * không thuộc cột nào (C-05) nên gửi kèm cột là máy chủ trả 400.
   */
  move: (taskId: number, sectionId: number | null, beforeTaskId: number | null) =>
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

  /**
   * Đặt giá trị cho một trường tùy biến. `value` ĐA HÌNH theo kiểu trường
   * (id giá trị · mảng id · employee_id · số · chuỗi ngày · chữ); `null` = bỏ
   * chọn. Máy chủ kiểm kiểu theo `field_type` — xem `label_value_service`.
   */
  setLabel: (taskId: number, fieldId: number, value: unknown) =>
    apiPut<WorkTask>(`/api/work/tasks/${taskId}/label`, {
      field_id: fieldId,
      value,
    }),

  /**
   * Nối việc trước → việc sau trên Gantt (B-15). Không có endpoint ĐỌC riêng:
   * mũi tên đi kèm `board` để biểu đồ có thanh và mũi tên trong một nhịp.
   *
   * Máy chủ trả 400 khi nối tạo vòng lặp, nối chính mình, trùng cặp, dính việc
   * con, hoặc hai đầu khác dự án — thông báo hiện thẳng bằng toast của `@/core/api`.
   */
  createLink: (values: {
    predecessor_id: number
    successor_id: number
    link_type?: number
    lag_days?: number
  }) => apiPost<WorkTaskLink>('/api/work/task-links', values),

  /**
   * Đổi KIỂU (FS/SS/FF/SF) hoặc độ trễ của một mũi tên đã có. Đổi hai đầu thì
   * xóa rồi nối lại — máy chủ không nhận, xem `TaskLinkUpdate`.
   */
  updateLink: (linkId: number, values: { link_type?: number; lag_days?: number }) =>
    apiPatch<WorkTaskLink>(`/api/work/task-links/${linkId}`, values),

  removeLink: (linkId: number) => apiDelete(`/api/work/task-links/${linkId}`),
}
