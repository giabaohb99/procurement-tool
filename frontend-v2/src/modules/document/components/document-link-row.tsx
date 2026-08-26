import { AlertTriangle, ArrowDownLeft, ArrowUpRight, Lock, X } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { HelpHint } from '@/shared/ui/help-hint'
import { RELATION_HINTS, type DocumentLink } from '../types/document-link'

interface DocumentLinkRowProps {
  link: DocumentLink
  onDelete?: (linkId: number) => void
}

/**
 * Một dòng quan hệ.
 *
 * Ba thứ phải đọc ra được mà KHÔNG cần nhìn tiêu đề thẻ chứa nó:
 *
 * 1. **quan hệ gì** — để thành huy hiệu chứ không phải chữ mờ lẫn vào tiêu đề;
 * 2. **chiều nào** — mũi tên đi ra / đi vào, vì hai thẻ trên trang trông y hệt
 *    nhau và người dùng cuộn tới giữa danh sách là mất tiêu đề thẻ;
 * 3. **văn bản nào** — kèm SỐ HIỆU và PHÁP NHÂN.
 *
 * ⚠️ Pháp nhân không phải chi tiết trang trí. Bản riêng của các pháp nhân con
 * chép nguyên tiêu đề của bản gốc và thường chưa cấp số, nên thiếu cột này thì
 * ba bản riêng của ABA · SAM · AGRIPLANT hiện ra ba dòng KHÔNG THỂ phân biệt —
 * đúng lỗi đã bắt được ở cây tài liệu (xem `CloneLink` trong `document-tree-card`).
 *
 * Nút gỡ chỉ hiện với quan hệ **đi ra** và **không phải hệ thống tạo**:
 *  - chiều đi vào là dữ liệu của văn bản bên kia, gỡ từ đây là sửa hồ sơ người khác;
 *  - dòng `is_system` (trích từ, clone) mà gỡ được thì văn bản con thành mồ côi.
 */
export function DocumentLinkRow({ link, onDelete }: DocumentLinkRowProps) {
  const other = link.document
  const leave = link.direction === 'outgoing'
  const removable = onDelete && leave && !link.is_system
  const Arrow = leave ? ArrowUpRight : ArrowDownLeft

  return (
    <li className="flex items-start gap-3 py-3 first:pt-0">
      <Arrow
        className="mt-0.5 size-4 shrink-0 text-muted-foreground"
        aria-label={leave ? 'Văn bản này trỏ tới' : 'Trỏ tới văn bản này'}
      />

      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          {/*  Huy hiệu chứ không phải chữ mờ: đây là thứ người ta lướt mắt tìm
               khi một văn bản có tám dòng quan hệ đủ loại.
               Kèm nút `?`: mười cái tên quan hệ nghe gần giống nhau, mà nhãn
               này còn được ĐỌC NGƯỢC theo phía đang xem ("Là căn cứ của" ở đây
               là mặt sau của "Căn cứ theo" bên kia) nên càng khó đoán nghĩa. */}
          <span className="flex items-center gap-1">
            <Badge variant="secondary" className="font-normal">
              {link.relation_label}
            </Badge>
            <HelpHint label={`Quan hệ «${link.relation_label}» nghĩa là gì`}>
              {RELATION_HINTS[link.relation]}
            </HelpHint>
          </span>

          {other ? (
            <Link
              to={appRoutes.document.documentDetail(other.id)}
              className="text-sm font-medium hover:underline"
            >
              {other.display_code ? `${other.display_code} · ` : ''}
              {other.title}
            </Link>
          ) : (
            <span className="text-sm italic text-muted-foreground">văn bản đã bị xóa</span>
          )}

          {link.is_system && (
            <span
              className="flex items-center gap-1 text-xs text-muted-foreground"
              title="Hệ thống tự tạo quan hệ này (bản trích, bản riêng) — không gỡ tay được."
            >
              <Lock className="size-3.5" />
              hệ thống tạo
            </span>
          )}
        </div>

        {other && (
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
            <Badge variant="outline" className="font-normal">
              {other.status_label}
            </Badge>
            {other.version_no && <span>bản {other.version_no}</span>}
            {!other.display_code && <span>· chưa cấp số</span>}
            {/*  Xem cảnh báo ở đầu tệp — cột phân biệt các bản riêng trùng tên. */}
            {other.company_name && <span>· {other.company_name}</span>}
            {link.note && <span>· {link.note}</span>}
          </p>
        )}

        {/*  Bản trích đang bám theo một phiên bản CŨ của gốc — nó có thể đang
             nói sai. Đây là hệ quả nhìn thấy được của E11 (a). */}
        {link.is_outdated && (
          <p className="flex items-center gap-1.5 text-xs text-amber-800">
            <AlertTriangle className="size-3.5 shrink-0 text-amber-700" />
            Bản gốc đã lên phiên bản mới sau lần trích này — cần rà lại.
          </p>
        )}
      </div>

      {removable && (
        <ConfirmIconButton
          icon={X}
          title="Gỡ quan hệ"
          destructive
          confirmTitle="Gỡ quan hệ này?"
          confirmDescription="Chỉ gỡ liên kết, hai văn bản vẫn còn nguyên."
          confirmLabel="Gỡ"
          onConfirm={() => onDelete(link.id)}
        />
      )}
    </li>
  )
}
