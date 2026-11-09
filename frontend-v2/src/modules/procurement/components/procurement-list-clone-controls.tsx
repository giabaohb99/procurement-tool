import { Copy } from 'lucide-react'
import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { httpClient } from '@/core/api/http-client'
import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'

interface ProcurementListCloneModeButtonProps {
  /** Đang ở chế độ nhân bản (cột *Thao tác* đang hiện). */
  active: boolean
  onToggle: () => void
  className?: string
}

/**
 * Nút bật / tắt CHẾ ĐỘ NHÂN BẢN ở đầu bốn danh sách Thu mua — đúng bản v1
 * (`CrudList.tsx`, duoc-CR-741): bấm *Nhân bản* thì hiện cột *Thao tác* có nút
 * nhân bản từng phiếu, bấm *Xong* thì cột ẩn đi. Để cột nằm sẵn mọi lúc thì một cú
 * bấm trượt trên bảng là đẻ ra phiếu nháp không ai muốn.
 */
export function ProcurementListCloneModeButton({
  active,
  onToggle,
  className,
}: ProcurementListCloneModeButtonProps) {
  return (
    <Button
      type="button"
      variant={active ? 'default' : 'outline'}
      aria-pressed={active}
      title="Bật chế độ nhân bản: hiện cột Thao tác để nhân bản từng phiếu"
      className={className}
      onClick={onToggle}
    >
      <Copy className="mr-1.5 size-4" />
      {active ? 'Xong' : 'Nhân bản'}
    </Button>
  )
}

interface ProcurementListCloneRowButtonProps {
  /** Đường API của chứng từ, vd `/api/purchase-requests` — gọi `POST <apiPath>/<id>/clone`. */
  apiPath: string
  id: number
  code?: string
  /** Đường trang chi tiết của phiếu MỚI tạo ra. */
  toDetail: (id: number) => string
  /** Câu báo khi backend không gửi kèm lời nhắn. */
  successMessage: string
  errorMessage: string
}

/**
 * Nút có chữ *Nhân bản* trong cột *Thao tác* — hỏi lại bằng đúng hộp *Nhân bản phiếu*
 * của bản v1 rồi mới tạo phiếu nháp mới và mở thẳng phiếu đó.
 */
export function ProcurementListCloneRowButton({
  apiPath,
  id,
  code,
  toDetail,
  successMessage,
  errorMessage,
}: ProcurementListCloneRowButtonProps) {
  const navigate = useNavigate()
  //  Chặn bấm đúp ngay trong tick — `disabled` theo state chỉ có hiệu lực ở lượt render sau.
  const busyRef = useRef(false)

  async function cloneRow() {
    if (busyRef.current) return
    const ok = await confirm({
      title: 'Nhân bản phiếu',
      message:
        `Bạn chắc chắn muốn nhân bản ${code ? `phiếu "${code}"` : 'phiếu này'}?\n\n` +
        'Hệ thống sẽ tạo một phiếu MỚI ở trạng thái Nháp. Phiếu mới độc lập, ' +
        'KHÔNG giữ liên kết khảo sát / đơn mua hàng / phê duyệt của phiếu gốc.',
      confirmLabel: 'Nhân bản',
      cancelLabel: 'Hủy',
      tone: 'default',
    })
    if (!ok) return
    busyRef.current = true
    trackUiAction(UI_ACTION_CODE.COPY_DOCUMENT)
    try {
      const res = await httpClient.post<{ message?: string; data: { id: number } }>(
        `${apiPath}/${id}/clone`,
      )
      toast.success(res.data?.message || successMessage)
      const newId = res.data?.data?.id
      if (newId) navigate(toDetail(newId))
    } catch {
      toast.error(errorMessage)
    } finally {
      busyRef.current = false
    }
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      title="Nhân bản thành phiếu nháp mới"
      //  Chữ hiện vẫn là *Nhân bản* như v1; tên đọc kèm mã phiếu để trình đọc màn hình phân
      //  biệt được nút của từng dòng (rà mã duoc-CR-741).
      aria-label={code ? `Nhân bản ${code}` : 'Nhân bản'}
      className="h-7 gap-1 px-2.5"
      onClick={(event) => {
        //  Ô nằm trong dòng có `onRowClick` (mở chi tiết) — chặn nổi bọt.
        event.stopPropagation()
        void cloneRow()
      }}
    >
      <Copy className="size-4" />
      Nhân bản
    </Button>
  )
}
