import { X } from 'lucide-react'
import { useMemo } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { LinesTable } from '@/shared/data-table/lines-table'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'

/**
 * Dòng đang chỉnh trên phiếu YCTT — hình dạng chung cho cả màn TẠO và màn XEM.
 *
 * `due_date` / `payable_total` / `payable_paid` đọc từ Công nợ, luôn chỉ hiển thị.
 */
export interface EditablePaymentLine {
  /** Khóa React ổn định — dòng chưa lưu chưa có id. */
  key: string
  payable_id: number
  supplier_code: string
  supplier_name: string
  source_type: string
  po_code: string
  /** bao-CR-304 (ticket 26) — mã MISA của ĐMH, chỉ hiển thị; đổi mã PO thì cập nhật sau khi Lưu. */
  misa_code: string
  invoice_no: string
  invoice_date: string
  due_date: string
  payable_total: number
  payable_paid: number
  amount: number
  /** CR-260 — phần đề nghị cấn trừ tiền treo, backend thực thi khi phiếu được Duyệt. */
  offset_amount: number
}

interface PaymentRequestLinesTableProps {
  rows: EditablePaymentLine[]
  editable: boolean
  storageKey: string
  /**
   * Hiện thêm hai cột Nhà cung cấp / Loại nợ. Bật ở màn TẠO (một phiếu có thể gộp
   * nhiều khoản); màn XEM cả phiếu là một NCC nên không cần.
   */
  showSupplierColumns: boolean
  /** Khóa PO của dòng đã gắn khoản nợ — chỉ dòng gõ tay mới cho sửa PO (màn TẠO). */
  lockLinkedPo: boolean
  /**
   * CR-260 — hiện cột "Cấn trừ trả trước". Chỉ bật khi phiếu có dòng mang phần
   * cấn trừ (hoặc đang sửa nháp có tiền treo) để phiếu thường không dài thêm cột.
   */
  showOffsetColumn: boolean
  supplierDisplay: (row: EditablePaymentLine) => string
  sourceDisplay: (row: EditablePaymentLine) => string
  onPatch: (index: number, patch: Partial<EditablePaymentLine>) => void
  onRemove: (index: number) => void
}

export function PaymentRequestLinesTable({
  rows,
  editable,
  storageKey,
  showSupplierColumns,
  lockLinkedPo,
  showOffsetColumn,
  supplierDisplay,
  sourceDisplay,
  onPatch,
  onRemove,
}: PaymentRequestLinesTableProps) {
  const isMobile = useIsMobile()
  const columns = useMemo<LinesTableColumn[]>(() => {
    const cols: LinesTableColumn[] = [
      { key: 'no', header: '#', width: 44, minWidth: 40, hideable: false, defaultPinned: true, align: 'center' },
    ]
    if (showSupplierColumns) {
      cols.push(
        { key: 'supplier', header: 'Nhà cung cấp', width: 260, minWidth: 160, wrap: true },
        { key: 'source', header: 'Loại nợ', width: 120, minWidth: 90 },
      )
    }
    //  ⚠️ **Nhóm cột PHỤ khai `compactHidden`** — bảng này 10 cột, bề rộng tự
    //  nhiên **1270px**; trong khung 356px của điện thoại thì nhìn thấy đúng ba
    //  cột đầu, còn ô *Đề nghị trả* — thứ duy nhất phải GÕ — nằm ngoài mép
    //  phải. Xương sống của một dòng đề nghị chi là: *PO nào · hóa đơn nào ·
    //  trả bao nhiêu*; bốn cột còn lại (mã MISA, ngày hóa đơn, hạn trả, tổng nợ
    //  / đã trả) là số liệu ĐỐI CHIẾU — cần khi ngồi soát, không cần lúc lập
    //  phiếu. Rút gọn xuống 5 cột / 570px.
    //
    //  Đây là cơ chế có sẵn của `LinesTable`, không phải khuôn mới: nút *Bảng
    //  đầy đủ* bung lại đúng nhóm này. Và nó chỉ bật mặc định ở khổ hẹp — xem
    //  `defaultCompact` bên dưới.
    cols.push(
      { key: 'po', header: 'PO', width: 150, minWidth: 90 },
      // bao-CR-304 (ticket 26) — cột Mã MISA chỉ hiển thị, mã nhập/sửa trên ĐMH.
      { key: 'misa', header: 'Mã MISA', width: 140, minWidth: 90, compactHidden: true },
      { key: 'invoice_no', header: 'Số hóa đơn', width: 160, minWidth: 100 },
      { key: 'invoice_date', header: 'Ngày hóa đơn', control: 'date', width: 160, compactHidden: true },
      {
        key: 'due_date',
        header: 'Hạn trả',
        width: 120,
        minWidth: 90,
        align: 'center',
        compactHidden: true,
      },
      {
        key: 'payable_total',
        header: 'Tổng nợ',
        width: 140,
        minWidth: 90,
        align: 'right',
        compactHidden: true,
      },
      {
        key: 'payable_paid',
        header: 'Đã trả',
        width: 140,
        minWidth: 90,
        align: 'right',
        compactHidden: true,
      },
    )
    if (showOffsetColumn) {
      cols.push({ key: 'offset', header: 'Cấn trừ trả trước', width: 160, minWidth: 110, align: 'right' })
    }
    cols.push(
      { key: 'amount', header: 'Đề nghị trả', width: 160, minWidth: 110, align: 'right' },
    )
    if (editable) {
      cols.push({ key: 'action', header: 'Bỏ', width: 56, minWidth: 44, hideable: false, align: 'center' })
    }
    return cols
  }, [showSupplierColumns, showOffsetColumn, editable])

  function renderCell(key: string, row: EditablePaymentLine, index: number) {
    const poEditable = editable && (!lockLinkedPo || !row.payable_id)

    switch (key) {
      case 'no':
        return <span className="text-muted-foreground">{index + 1}</span>

      case 'supplier':
        return (
          <span className="block break-words leading-snug" title={supplierDisplay(row)}>
            {supplierDisplay(row) || '—'}
          </span>
        )

      case 'source':
        return sourceDisplay(row) || '—'

      case 'po':
        return poEditable ? (
          <Input
            value={row.po_code}
            placeholder="Mã PO"
            onChange={(e) => onPatch(index, { po_code: e.target.value })}
          />
        ) : (
          row.po_code || '—'
        )

      case 'misa':
        return row.misa_code || '—'

      case 'invoice_no':
        return editable ? (
          <Input
            value={row.invoice_no}
            placeholder="(để trống = in tay)"
            onChange={(e) => onPatch(index, { invoice_no: e.target.value })}
          />
        ) : (
          row.invoice_no || <span className="text-xs text-destructive">chưa có HĐ</span>
        )

      case 'invoice_date':
        return editable ? (
          <DatePicker
            size="sm"
            value={row.invoice_date}
            onChange={(v) => onPatch(index, { invoice_date: v })}
          />
        ) : (
          formatDate(row.invoice_date) || '—'
        )

      case 'due_date':
        return <span className="text-muted-foreground">{formatDate(row.due_date) || '—'}</span>

      case 'payable_total':
        return <span className="tabular-nums">{formatMoney(row.payable_total)}</span>

      case 'payable_paid':
        return <span className="tabular-nums">{formatMoney(row.payable_paid)}</span>

      case 'offset':
        // CR-260 — ý định cấn trừ tiền treo: nháp sửa được, duyệt xong chỉ xem
        return editable ? (
          <Input
            type="number"
            className="w-full px-2 text-right tabular-nums"
            value={row.offset_amount ?? 0}
            onChange={(e) => onPatch(index, { offset_amount: Number(e.target.value) || 0 })}
          />
        ) : (
          <span className="tabular-nums text-primary">{formatMoney(row.offset_amount)}</span>
        )

      case 'amount':
        return editable ? (
          <Input
            type="number"
            className="w-full px-2 text-right tabular-nums"
            value={row.amount ?? 0}
            onChange={(e) => onPatch(index, { amount: Number(e.target.value) || 0 })}
          />
        ) : (
          <span className="font-semibold tabular-nums">{formatMoney(row.amount)}</span>
        )

      case 'action':
        return (
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-destructive hover:text-destructive"
            title="Bỏ dòng này khỏi phiếu"
            onClick={() => onRemove(index)}
          >
            <X />
          </Button>
        )

      default:
        return null
    }
  }

  return (
    <LinesTable
      //  ⚠️ Rút gọn CHỈ ở khổ điện thoại, không áp cho màn rộng. Kế toán ngồi
      //  máy tính cần đúng mấy cột đối chiếu (tổng nợ · đã trả · hạn trả) để
      //  soát trước khi ký; bật mặc định cho họ là lấy đi thứ họ đang dùng, mà
      //  bảng ở đó tuy có cuộn ngang thì vẫn đọc được. Trên điện thoại thì
      //  ngược lại: 10 cột / 1270px trong khung 356px là không dùng nổi.
      //
      //  Chỉ là MẶC ĐỊNH lần đầu: ai đã tự chỉnh bố cục thì bản lưu trong
      //  `localStorage` (`erp.table.<storageKey>`) vẫn thắng, nên sửa dòng này
      //  mà màn hình không đổi thì xóa khóa đó rồi thử lại chứ không phải mã sai.
      defaultCompact={isMobile}
      columns={columns}
      rows={rows}
      storageKey={storageKey}
      rowKey={(row) => row.key}
      renderCell={renderCell}
      title={`Các khoản công nợ thanh toán (${rows.length})`}
      emptyMessage="Chưa có dòng nào."
      cellClassName={(key) => (key === 'amount' ? 'bg-warning/8' : undefined)}
    />
  )
}
