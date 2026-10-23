import { RotateCw, TriangleAlert } from 'lucide-react'

import { EmployeePeopleEditor } from './employee-people-editor'
import { FAMILY_COLUMNS, createEmptyFamilyRow } from '../config/employee-family-columns'
import type { EmployeeFamily } from '../types/employee'
import { Button } from '@/shared/ui/button'

interface SelfChangeRequestFamiliesTabProps {
  /** Danh sách hiện tại từ `/me/families`; `undefined` = chưa có (đang nạp hoặc lỗi). */
  families: EmployeeFamily[] | undefined
  familiesLoading: boolean
  familiesError: boolean
  onRetry: () => void
  /** Nháp người dùng đã sửa; `null` = chưa đụng. */
  draft: EmployeeFamily[] | null
  onDraftChange: (rows: EmployeeFamily[]) => void
}

/**
 * Tab «Hộ gia đình» của hộp «Đề nghị sửa thông tin» (duoc-CR-676).
 *
 * ⚠️ Nạp `/me/families` HỎNG thì KHÔNG dựng bảng sửa (review M4). Dựng bảng rỗng thì người dùng
 * tưởng hộ chưa khai ai, thêm một người, gửi đi — đề nghị THAY CẢ danh sách nên duyệt xong là mọi
 * thành viên thật bị xóa. Thay bằng câu báo lỗi + nút thử lại; các tab khác vẫn gửi được.
 */
export function SelfChangeRequestFamiliesTab({
  families,
  familiesLoading,
  familiesError,
  onRetry,
  draft,
  onDraftChange,
}: SelfChangeRequestFamiliesTabProps) {
  if (familiesError && families === undefined) {
    return (
      <div
        role="alert"
        className="flex flex-col items-start gap-3 rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm"
      >
        <p className="flex items-start gap-2">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
          Không tải được danh sách hộ gia đình hiện tại, nên chưa sửa được phần này — gửi lúc này có
          thể xóa nhầm thành viên đang có. Các tab khác vẫn gửi được bình thường.
        </p>
        <Button type="button" variant="outline" size="sm" onClick={onRetry}>
          <RotateCw className="size-4" />
          Thử tải lại
        </Button>
      </div>
    )
  }

  return (
    <EmployeePeopleEditor<EmployeeFamily>
      title="Thành viên hộ gia đình"
      description="Dùng cho hồ sơ bảo hiểm xã hội. Quan hệ ghi theo chủ hộ. Danh sách gửi đi thay cho danh sách hiện tại khi được duyệt."
      columns={FAMILY_COLUMNS}
      //  Đưa NHÁP vào lại: Radix hủy mount tab ẩn, sang tab khác rồi quay lại mà nạp từ
      //  `families` gốc thì màn hiện danh sách cũ trong khi nút Gửi vẫn gửi bản đã sửa.
      rows={draft ?? families}
      isLoading={familiesLoading}
      emptyRow={createEmptyFamilyRow}
      canWrite
      isSaving={false}
      onSave={() => undefined}
      onDraftChange={onDraftChange}
    />
  )
}
