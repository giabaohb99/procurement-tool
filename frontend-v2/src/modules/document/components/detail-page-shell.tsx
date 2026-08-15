import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import type { HistoryEntry } from '../store/local-collection'
import { RecordHistoryCard } from './record-history-card'

interface DetailPageShellProps {
  title: string
  description?: ReactNode
  /** Id của thẻ `<form>` bên trong `children` — nút Lưu trên header trỏ về đây. */
  formId: string
  /** Đang thêm mới: không có nút xóa và chưa có lịch sử để xem. */
  isCreating: boolean
  /** Đường dẫn danh sách của danh mục này. */
  backTo: string
  /** Bản ghi không tồn tại (link cũ của bản ghi đã xóa). */
  isMissing?: boolean
  missingTitle?: string
  onDelete?: () => void
  deleteConfirmTitle?: string
  deleteConfirmDescription?: string
  /**
   * Thay cụm Hủy / Lưu mặc định.
   *
   * Dùng cho trang có nhiều tab, mỗi tab lưu một thứ khác nhau — lúc đó một nút
   * "Lưu" chung trên đầu trang không còn rõ là đang lưu cái gì.
   */
  actions?: ReactNode
  history: HistoryEntry[]
  /**
   * Ẩn hẳn khối "Lịch sử thao tác".
   *
   * Cho trang có tab mà một trong số đó là màn làm việc toàn màn hình (soạn
   * thảo): ở đó khối lịch sử chỉ đẩy trang giấy lên và cắt mất chỗ gõ.
   */
  showHistory?: boolean
  children: ReactNode
}

/**
 * Khung chung cho MỌI trang chi tiết của phân hệ Văn bản.
 *
 * Gom về một chỗ ba thứ mà trang nào cũng phải có và rất dễ làm lệch nhau:
 * nút quay lại nằm cạnh tiêu đề, cụm Hủy/Lưu/Xóa trên đầu trang, và khối
 * "Lịch sử thao tác" ở cuối.
 */
export function DetailPageShell({
  title,
  description,
  formId,
  isCreating,
  backTo,
  isMissing,
  missingTitle = 'Không tìm thấy bản ghi',
  onDelete,
  deleteConfirmTitle,
  deleteConfirmDescription,
  actions,
  history,
  showHistory = true,
  children,
}: DetailPageShellProps) {
  const navigate = useNavigate()
  const back = () => navigate(backTo)

  if (isMissing) {
    return (
      <ErrorState
        code="404"
        title={missingTitle}
        description="Bản ghi này không tồn tại hoặc đã bị xóa."
      >
        <Button onClick={back}>
          <ArrowLeft className="size-4" />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  return (
    <PageContainer className="space-y-5">
      <PageHeader
        title={title}
        description={description}
        leading={
          // Chỉ icon: đứng sát tiêu đề thì mũi tên đã đủ nghĩa "lùi ra danh
          // sách", thêm chữ chỉ đẩy tiêu đề đi xa.
          <Button
            variant="outline"
            size="icon"
            title="Về danh sách"
            aria-label="Về danh sách"
            onClick={back}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        actions={
          <>
            {!isCreating && onDelete && (
              <ConfirmIconButton
                icon={Trash2}
                title="Xóa"
                destructive
                confirmTitle={deleteConfirmTitle ?? `Xóa "${title}"?`}
                confirmDescription={
                  deleteConfirmDescription ?? 'Thao tác này không hoàn tác được.'
                }
                confirmLabel="Xóa"
                onConfirm={onDelete}
              />
            )}

            {/* So sánh với `undefined` chứ không dùng `??`: trang tab nào tự lo
                nút lưu thì truyền `null` để KHÔNG hiện cụm mặc định. */}
            {actions !== undefined ? (
              actions
            ) : (
              <>
                <Button variant="outline" onClick={back}>
                  Hủy
                </Button>
                {/* Nút Lưu đứng ngoài form, nối vào bằng `form=`. */}
                <Button type="submit" form={formId}>
                  <Save className="size-4" />
                  Lưu
                </Button>
              </>
            )}
          </>
        }
      />

      {children}

      {/* Chỉ bản ghi đã tồn tại mới có lịch sử để xem. */}
      {!isCreating && showHistory && <RecordHistoryCard entries={history} />}
    </PageContainer>
  )
}
