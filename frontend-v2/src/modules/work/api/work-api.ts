import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type {
  WorkLabelField,
  WorkLabelOption,
  WorkList,
  WorkMember,
  WorkSection,
  WorkSidebar,
} from '../types/work'

/**
 * Nhóm · danh sách công việc · cấu hình của list.
 *
 * Prefix `/api/work` chứ không `/api/tasks` — đường đó là của tab «Việc cần làm»
 * (CR-215), trùng vào là lẫn hai thứ khác hẳn nhau.
 */
export const workApi = {
  /** Cây điều hướng: nhóm → nhóm con → list, kèm list đứng lẻ (A-05). */
  sidebar: (includeArchived = false) =>
    apiGet<WorkSidebar>('/api/work/groups', {
      params: { include_archived: includeArchived },
    }),

  createGroup: (values: { name: string; description?: string; parent_id?: number | null }) =>
    apiPost('/api/work/groups', values),

  updateGroup: (id: number, values: Record<string, unknown>) =>
    apiPatch(`/api/work/groups/${id}`, values),

  /** "Xóa" nhóm = lưu trữ (A-01) — backend không xóa cứng. */
  archiveGroup: (id: number) => apiDelete(`/api/work/groups/${id}`),

  groupMembers: (groupId: number) =>
    apiGet<WorkMember[]>(`/api/work/groups/${groupId}/members`),

  addGroupMember: (groupId: number, values: { employee_id: number; role: number }) =>
    apiPost<WorkMember>(`/api/work/groups/${groupId}/members`, values),

  removeGroupMember: (groupId: number, memberId: number) =>
    apiDelete(`/api/work/groups/${groupId}/members/${memberId}`),

  /** `withPeople` nạp thêm chủ sở hữu + thành viên — chỉ màn liệt kê dự án cần. */
  lists: (includeArchived = false, withPeople = false) =>
    apiGet<WorkList[]>('/api/work/lists', {
      params: { include_archived: includeArchived, with_people: withPeople },
    }),

  createList: (values: { name: string; description?: string; group_id?: number | null }) =>
    apiPost<WorkList>('/api/work/lists', values),

  getList: (id: number) => apiGet<WorkList>(`/api/work/lists/${id}`),

  updateList: (id: number, values: Record<string, unknown>) =>
    apiPatch<WorkList>(`/api/work/lists/${id}`, values),

  archiveList: (id: number) => apiDelete(`/api/work/lists/${id}`),

  /** Kéo đổi thứ tự CỘT — trả cả hàng cột đã xếp lại (xem `move_section`). */
  moveSection: (sectionId: number, beforeSectionId: number | null) =>
    apiPost<WorkSection[]>(`/api/work/sections/${sectionId}/move`, {
      before_section_id: beforeSectionId,
    }),

  members: (listId: number) => apiGet<WorkMember[]>(`/api/work/lists/${listId}/members`),

  addMember: (listId: number, values: { employee_id: number; role: number }) =>
    apiPost<WorkMember>(`/api/work/lists/${listId}/members`, values),

  removeMember: (listId: number, memberId: number) =>
    apiDelete(`/api/work/lists/${listId}/members/${memberId}`),

  leaveList: (listId: number) => apiPost(`/api/work/lists/${listId}/leave`, {}),

  sections: (listId: number) => apiGet<WorkSection[]>(`/api/work/lists/${listId}/sections`),

  createSection: (listId: number, values: { name: string; color?: string; sort_order?: number }) =>
    apiPost<WorkSection>(`/api/work/lists/${listId}/sections`, values),

  updateSection: (sectionId: number, values: Record<string, unknown>) =>
    apiPatch<WorkSection>(`/api/work/sections/${sectionId}`, values),

  /** Cột còn việc thì BẮT BUỘC kèm `moveTo` — backend chặn, không cho task mồ côi. */
  deleteSection: (sectionId: number, moveTo?: number) =>
    apiDelete(`/api/work/sections/${sectionId}`, {
      params: moveTo ? { move_to: moveTo } : undefined,
    }),

  labelFields: (listId: number) =>
    apiGet<WorkLabelField[]>(`/api/work/lists/${listId}/label-fields`),

  /** `field_type` theo `WORK_FIELD_TYPE`; bỏ trống là «chọn một giá trị». */
  createLabelField: (listId: number, values: { name: string; field_type?: number }) =>
    apiPost<WorkLabelField>(`/api/work/lists/${listId}/label-fields`, values),

  /** Kiểu trường chỉ đổi được khi chưa có giá trị nào gán cho việc (backend chặn). */
  updateLabelField: (fieldId: number, values: { name?: string; field_type?: number }) =>
    apiPatch<WorkLabelField>(`/api/work/label-fields/${fieldId}`, values),

  deleteLabelField: (fieldId: number) => apiDelete(`/api/work/label-fields/${fieldId}`),

  createLabelOption: (
    fieldId: number,
    values: { name: string; color?: string; sort_order?: number },
  ) =>
    apiPost<WorkLabelOption>(`/api/work/label-fields/${fieldId}/options`, values),

  updateLabelOption: (
    optionId: number,
    values: { name?: string; color?: string; sort_order?: number },
  ) =>
    apiPatch<WorkLabelOption>(`/api/work/label-options/${optionId}`, values),

  deleteLabelOption: (optionId: number) => apiDelete(`/api/work/label-options/${optionId}`),
}
