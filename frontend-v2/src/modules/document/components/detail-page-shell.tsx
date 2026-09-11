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
                //  `max-md:size-9` cho nút này cao đúng 36px bằng Hủy/Lưu đứng
                //  cạnh. Mặc định nó 32px — lệch 4px giữa ba nút trên cùng một
                //  hàng, đủ để hàng nút đọc ra như xếp chưa thẳng.
                className="max-md:order-last max-md:size-9"
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
                {/*  ⚠️ **`max-md:hidden` — nút Hủy BIẾN MẤT ở khổ hẹp, và đây là
                     bỏ thứ THỪA chứ không phải giấu bớt cho gọn.** `onClick` của
                     nó là `back`, đúng cùng một hàm với nút `←` nằm ngay cạnh
                     tiêu đề phía trên — hai chỗ bấm cho cùng một việc, không
                     chỗ nào cảnh báo mất dữ liệu, khác nhau đúng ở chỗ đứng.

                     Trên màn rộng giữ lại vì đó là nếp quen của biểu mẫu và ở đó
                     nó không lấy chỗ của ai. Khổ hẹp thì cụm nút luôn xuống hàng
                     riêng (`max-md:w-full` của `PageHeader`), nên mỗi nút thừa
                     là một mẩu cắt ngang đúng cái hàng vốn đã chật.

                     ⚠️ **Vì sao phải bỏ hẳn chứ không chỉ dàn cho đều.** Bản
                     trước cho Hủy và Lưu chia đôi hàng: hết khoảng trống thật,
                     nhưng hàng thành BA khối rời cỡ khác nhau (160 · 150 · 36)
                     mà khối cuối lại là một biểu tượng đỏ — mắt đọc ra ba mẩu
                     cụt chứ không ra một cụm (khách báo 11/09/2026). Bỏ Hủy thì
                     còn đúng hai thứ, mỗi thứ một việc rõ ràng: **Lưu** trải hết
                     hàng (việc chính, vùng chạm rộng nhất) và **Xóa** giữ nguyên
                     ô vuông ở mép phải. */}
                <Button variant="outline" onClick={back} className="max-md:hidden">
                  Hủy
                </Button>
                {/*  Nút Lưu đứng ngoài form, nối vào bằng `form=`.
                     `max-md:flex-1`: chiếm trọn phần còn lại của hàng. */}
                <Button type="submit" form={formId} className="max-md:flex-1">
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
