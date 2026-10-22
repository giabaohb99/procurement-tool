/** Một dòng trong thùng rác của dự án (B-09) — khuôn `task_trash_service.list_trash`. */
export interface WorkTrashItem {
  id: number
  title: string
  /** `WORK_TASK_KIND`: việc thường hay cột mốc. */
  kind: number
  /** Có giá trị = đây là VIỆC CON bị xóa riêng; cha của nó vẫn còn sống. */
  parent_id: number | null
  parent_title: string
  deleted_at: string
  deleted_by_name: string
  /** Backend quyết: quản trị mọi việc, thành viên chỉ việc mình tạo, dự án lưu trữ thì khóa. */
  can_restore: boolean
}
