import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { AuditTimeline } from '@/shared/audit'
import type { HistoryEntry } from '../store/local-collection'
import { HeaderActionsPopover } from './header-actions-popover'
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
  /**
   * Class thêm cho CỤM NÚT trên đầu trang (`PageHeaderProps.actionsClassName`).
   *
   * Có để trang nhiều nút tự quyết cách bày ở khổ hẹp. Mặc định `PageHeader` căn
   * `justify-end`: đúng khi cụm chỉ có một hai nút, nhưng trang nào tràn xuống
   * ba hàng thì mỗi hàng lại bắt đầu ở một mốc khác nhau — đo ở màn Văn bản là
   * các khe trái 310 · 21 · 89 · 228px, đọc ra như mấy nút rơi vãi chứ không ra
   * một cụm. Trang đó truyền `max-md:justify-start` để mọi hàng thẳng một mép.
   */
  actionsClassName?: string
  /**
   * Lệnh PHỤ của đầu trang — khổ hẹp gom vào nút `⋯`, màn rộng bày thẳng ra
   * hàng như cũ. Nút XÓA tự đi theo nhóm này, trang không phải tự lo.
   *
   * Chia theo dáng nút: `variant="default"` (việc người dùng đang định làm) để
   * ở `actions`, mấy nút viền cho vào đây — xem `HeaderActionsPopover`.
   */
  secondaryActions?: ReactNode
  /**
   * Nhật ký của kho tạm phía trình duyệt. Chỉ còn các màn CHƯA nối API dùng —
   * màn đã có backend thì truyền `audit` để đọc `tab_audit_log` thật.
   */
  history?: HistoryEntry[]
  /** Bản ghi đã có backend: đọc nhật ký thật theo `(entity, id)`. */
  audit?: { entity: string; id: number }
  /**
   * Ẩn hẳn khối "Lịch sử thao tác".
   *
   * Cho trang có tab mà một trong số đó là màn làm việc toàn màn hình (soạn
   * thảo): ở đó khối lịch sử chỉ đẩy trang giấy lên và cắt mất chỗ gõ.
   */
  showHistory?: boolean
  /**
   * Dính dải tiêu đề lên đầu khung khi cuộn.
   *
   * Chỉ bật cho màn có form DÀI mà nút bấm nằm trên đầu (tab Thông tin). Màn
   * làm việc toàn màn hình như soạn thảo thì không: ở đó phần cuộn nằm bên
   * trong trang giấy, dải dính chỉ ăn mất chiều cao.
   */
  stickyHeader?: boolean
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
  actionsClassName,
  secondaryActions,
  history,
  audit,
  showHistory = true,
  stickyHeader = false,
  children,
}: DetailPageShellProps) {
  const navigate = useNavigate()
  const back = () => navigate(backTo)
  const isMobile = useIsMobile()

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
        sticky={stickyHeader}
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
        actionsClassName={actionsClassName}
        actions={
          <>
            {/*  ⚠️ `max-md:order-last` — ở khổ hẹp nút XÓA phải đứng CUỐI cụm.
                 Nó khai trước trong mã vì trên màn rộng cụm nút căn phải, nên
                 "đầu danh sách" hiện ra ở mép trái, xa nhất khỏi nút chính. Khổ
                 hẹp thì cụm dồn trái và thứ tự đảo nghĩa: một nút XÓA (không
                 hoàn tác được) nằm ngay đầu hàng, sát chỗ ngón cái quen bấm
                 «Tệp» / «Lưu». Đẩy về cuối để nó ở xa nhịp thao tác thường ngày.

                 Trang nào khai `secondaryActions` thì nút này KHÔNG đứng ở đây
                 nữa — nó theo nhóm phụ vào trong `⋯` (xem cuối khối này). */}
            {!isCreating && onDelete && !secondaryActions && (
              <ConfirmIconButton
                className="max-md:order-last"
                icon={Trash2}
                title="Xóa"
                destructive
                confirmTitle={deleteConfirmTitle ?? `Xóa "${title}"?`}
                confirmDescription={deleteConfirmDescription ?? 'Thao tác này không hoàn tác được.'}
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

            {/*  Nhóm lệnh PHỤ. Dựng MỘT LẦN rồi để `useIsMobile` chọn khung bọc —
                 KHÔNG dựng hai bản rồi ẩn một bằng CSS: mấy nút này mang hộp
                 thoại và truy vấn riêng (menu *Tệp*, *Chữ ký*, *Sao chép*), bản
                 ẩn vẫn gắn kết và vẫn gọi API, chỉ là không ai thấy. */}
            {secondaryActions &&
              (isMobile ? (
                <HeaderActionsPopover>
                  {secondaryActions}
                  {!isCreating && onDelete && (
                    <ConfirmIconButton
                      icon={Trash2}
                      title="Xóa"
                      label="Xóa"
                      destructive
                      confirmTitle={deleteConfirmTitle ?? `Xóa "${title}"?`}
                      confirmDescription={
                        deleteConfirmDescription ?? 'Thao tác này không hoàn tác được.'
                      }
                      confirmLabel="Xóa"
                      onConfirm={onDelete}
                    />
                  )}
                </HeaderActionsPopover>
              ) : (
                <>
                  {secondaryActions}
                  {/*  `md:order-first` trả nút XÓA về đầu cụm như trước khi tách
                       nhóm. Cụm nút của màn rộng căn PHẢI, nên "đầu cụm" hiện ra
                       ở mép trái — xa nhất khỏi mấy nút hay bấm. Khai ở cuối mã
                       (để nó đi theo nhóm phụ vào `⋯` ở khổ hẹp) mà không có lớp
                       này thì trên desktop nó dạt sang phải, nằm ngay cạnh «Gửi
                       duyệt»: một nút không hoàn tác được đứng sát nhịp thao tác
                       thường ngày. */}
                  {!isCreating && onDelete && (
                    <ConfirmIconButton
                      className="md:order-first"
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
                </>
              ))}
          </>
        }
      />

      {children}

      {/* Chỉ bản ghi đã tồn tại mới có lịch sử để xem.

          `showMessage`: với văn bản, TIN NẰM Ở CÂU chứ không ở nhãn hành động —
          «Trả về người nộp: sai thể thức», «Mở phiên bản 2.0: sửa điều 3». Tắt
          nó đi thì cả thẻ chỉ còn một cột «… — Cập nhật» lặp lại, đọc xong
          không biết chuyện gì đã xảy ra (khách báo 24/08/2026 là «không log»). */}
      {!isCreating && showHistory && audit && (
        <AuditTimeline entity={audit.entity} entityId={audit.id} showMessage />
      )}
      {!isCreating && showHistory && !audit && history && <RecordHistoryCard entries={history} />}
    </PageContainer>
  )
}
