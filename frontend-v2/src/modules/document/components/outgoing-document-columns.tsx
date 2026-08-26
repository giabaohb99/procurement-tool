import { ChevronRight, CornerDownRight, ShieldCheck } from 'lucide-react'
import { useCallback, useMemo } from 'react'

import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { DocumentCopyAction } from './document-copy-action'
import { effectiveLabel } from '../helpers/document-status'
import { useSecurityLevelLabel } from '../hooks/use-document-catalogs'
import {
  SECURITY_LEVEL_KIND_CONFIDENTIAL,
  SECURITY_LEVEL_KIND_URGENCY,
} from '../types/security-level'
import type { DocumentRecord } from '../types/document-record'

interface OutgoingColumnsOptions {
  /** Dòng đang bung để xem bản riêng — `null` là chưa bung dòng nào. */
  expandedRow: number | null
  setExpandedRow: (id: number | null) => void
  /** Id các văn bản đang chờ CHÍNH người đang xem duyệt. */
  awaitingMyApproval: Set<number>
  canCreate: boolean
}

/**
 * Cột của bảng VĂN BẢN ĐI.
 *
 * Tách khỏi tệp tab vì bộ cột này một mình đã dài hơn phần còn lại của màn, mà
 * hai thứ đổi vì lý do khác hẳn nhau: cột đổi khi nghiệp vụ thêm thông tin,
 * phần kia đổi khi cách lọc / phân trang đổi.
 *
 * Là HOOK chứ không phải hằng số như bảng hộp duyệt: mấy ô ở đây phụ thuộc
 * trạng thái của màn (dòng nào đang bung) và cả danh mục lấy từ máy chủ (mức
 * mật), nên không dựng sẵn lúc nạp module được.
 */
export function useOutgoingDocumentColumns({
  expandedRow,
  setExpandedRow,
  awaitingMyApproval,
  canCreate,
}: OutgoingColumnsOptions): DataTableColumn<DocumentRecord>[] {
  const securityLevelLabel = useSecurityLevelLabel()

  //  ⚠️ Phải chặn `dongDangBung === null`: `source_document_id` của văn bản
  //  thường cũng là `null`, mà `null === null` là TRUE — so thẳng thì lúc chưa
  //  bung dòng nào, CẢ BẢNG bị đánh dấu là bản riêng.
  const isExpandedChild = useCallback(
    (row: DocumentRecord) =>
      expandedRow !== null && row.source_document_id === expandedRow,
    [expandedRow],
  )

  return useMemo<DataTableColumn<DocumentRecord>[]>(
    () => [
      {
        key: 'display_code',
        header: 'Số hiệu',
        width: 210,
        hideable: false,
        defaultPinned: true,
        cell: (row) => {
          //  Chỉ thụt lề khi dòng CHA đang nằm ngay trên nó. Người ở pháp nhân
          //  con xem được bản riêng nhưng KHÔNG xem được bản gốc — với họ đây
          //  là văn bản đứng một mình, kẻ mũi tên rẽ nhánh là trỏ vào một dòng
          //  cha không tồn tại trên màn hình.
          const isPrivateCopy = isExpandedChild(row)
          const privateCopyCount = row.clone_count ?? 0

          return (
            <div className="flex items-center gap-1">
              {privateCopyCount > 0 ? (
                //  Nút bung phải chặn click lan lên dòng, nếu không mỗi lần mở
                //  nhánh là mở luôn trang chi tiết của bản gốc.
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  //  24px + `-my-px` chứ không để nguyên 32px của `icon-sm`: ô
                  //  bảng chỉ chừa 23px cho nội dung (`min-h-9` + `py-1.5`), nút
                  //  cao hơn là đội cả dòng lên — mà chỉ những dòng CÓ bản riêng
                  //  mới có nút này nên bảng còn so le cao thấp. Cùng cỡ với nút
                  //  sao chép ở cột Thao tác (`document-copy-action.tsx`).
                  className="-ml-1 -my-px size-6 shrink-0"
                  title={`${privateCopyCount} bản riêng ở pháp nhân con`}
                  aria-label={`Xem ${privateCopyCount} bản riêng`}
                  aria-expanded={expandedRow === row.id}
                  onClick={(event) => {
                    event.stopPropagation()
                    setExpandedRow(expandedRow === row.id ? null : row.id)
                  }}
                >
                  <ChevronRight
                    className={cn('transition-transform', expandedRow === row.id && 'rotate-90')}
                  />
                </Button>
              ) : (
                //  Chừa đúng chỗ của nút để cột số hiệu của mọi dòng thẳng hàng.
                //  `w-5` = 24px của nút trừ 4px `-ml-1` nó tự thụt vào.
                <span className={cn('shrink-0', isPrivateCopy ? 'w-3' : 'w-5')} />
              )}

              {isPrivateCopy && (
                <CornerDownRight className="size-3.5 shrink-0 text-muted-foreground" />
              )}

              <span
                className={cn(
                  'truncate',
                  isPrivateCopy ? 'text-muted-foreground' : 'font-medium text-navy',
                )}
              >
                {/* Chưa duyệt thì chưa có số — nói rõ chứ đừng để ô trống. */}
                {row.display_code || <span className="text-muted-foreground">Chưa cấp số</span>}
              </span>
            </div>
          )
        },
      },
      {
        key: 'book_number_display',
        header: 'Số vào sổ',
        width: 130,
        cell: (row) => <span className="tabular-nums">{row.book_number_display}</span>,
      },
      { key: 'title', header: 'Tên văn bản', width: 340, cell: (row) => row.title },
      {
        key: 'doc_type_name',
        header: 'Loại',
        width: 160,
        cell: (row) => row.doc_type_name,
      },
      {
        key: 'company_name',
        header: 'Pháp nhân ban hành',
        width: 220,
        cell: (row) => (
          //  Với BẢN RIÊNG đang bung, pháp nhân là thứ duy nhất phân biệt nó
          //  với bản gốc (tiêu đề chép nguyên) — tô đậm để mắt bám vào cột đó.
          <span className={cn('truncate', isExpandedChild(row) && 'font-medium')}>
            {row.company_name}
          </span>
        ),
      },
      {
        key: 'department_name',
        header: 'Phòng chủ trì',
        width: 170,
        cell: (row) => row.department_name,
      },
      {
        key: 'book_name',
        header: 'Sổ',
        width: 170,
        defaultHidden: true,
        cell: (row) => row.book_name,
      },
      {
        key: 'version_no',
        header: 'Bản',
        width: 90,
        align: 'right',
        cell: (row) => (
          <span className="tabular-nums">
            {row.version_no}
            {row.version_count > 1 && (
              <span className="text-muted-foreground"> /{row.version_count}</span>
            )}
          </span>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 190,
        // Nhãn TÍNH RA lúc hiển thị (hết hạn theo ngày), không phải trạng thái thô.
        cell: (row) => {
          const label = effectiveLabel(row)
          //  «Chờ bạn duyệt» đứng CẠNH trạng thái chứ không thay thế nó: văn bản
          //  vẫn đang ở «Đang duyệt», thứ thêm vào là *lượt của ai*. Đây là dấu
          //  để người duyệt nhặt ra dòng của mình giữa một bảng dài mà không
          //  phải mở từng cái.
          return (
            <div className="flex items-center gap-1.5">
              <Badge variant={label.variant}>{label.text}</Badge>
              {awaitingMyApproval.has(row.id) && (
                <Badge className="gap-1 bg-primary text-primary-foreground">
                  <ShieldCheck className="size-3" />
                  Chờ bạn duyệt
                </Badge>
              )}
            </div>
          )
        },
      },
      {
        key: 'effective_date',
        header: 'Ngày hiệu lực',
        width: 140,
        cell: (row) => formatDate(row.effective_date ?? ''),
      },
      {
        key: 'secrecy_level',
        header: 'Mức mật',
        width: 120,
        cell: (row) => (
          <Badge variant="outline" className="font-normal">
            {securityLevelLabel(SECURITY_LEVEL_KIND_CONFIDENTIAL, row.secrecy_level)}
          </Badge>
        ),
      },
      {
        key: 'urgency',
        header: 'Độ khẩn',
        width: 110,
        defaultHidden: true,
        cell: (row) => securityLevelLabel(SECURITY_LEVEL_KIND_URGENCY, row.urgency),
      },
      {
        key: 'owner_name',
        header: 'Người chịu trách nhiệm',
        width: 180,
        defaultHidden: true,
        cell: (row) => row.owner_name,
      },
      {
        key: 'legacy_code',
        header: 'Số hiệu cũ',
        width: 150,
        defaultHidden: true,
        cell: (row) => row.legacy_code,
      },
      {
        key: 'storage_location',
        header: 'Nơi lưu trữ cứng',
        width: 200,
        //  Ẩn mặc định: chỉ cần tới lúc đi lấy hồ sơ giấy hoặc kiểm kê kho,
        //  không phải thứ đọc hằng ngày.
        defaultHidden: true,
        cell: (row) => row.storage_location,
      },
      {
        key: 'attachment_count',
        header: 'Tệp',
        width: 80,
        align: 'right',
        cell: (row) => (row.attachment_count ? String(row.attachment_count) : ''),
      },
      {
        key: 'copy_action',
        header: 'Thao tác',
        width: 84,
        align: 'center',
        hideable: false,
        stickyRight: true,
        cell: (row) => (
          <DocumentCopyAction documentId={row.id} canCreate={canCreate} placement="row" />
        ),
      },
    ],
    [expandedRow, setExpandedRow, isExpandedChild, awaitingMyApproval, canCreate, securityLevelLabel],
  )
}
