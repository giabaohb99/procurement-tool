import { Check, CornerUpLeft } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import type { RecentPurchaseRequest } from '../api/procurement-dashboard-api'
import { usePurchaseRequestAction } from '../hooks/use-purchase-request'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import { StatusBadge } from './document-status-badge'

interface RecentPurchaseRequestsProps {
  rows: RecentPurchaseRequest[]
}

/**
 * Bảng "Yêu cầu mua gần đây" ở trang Tổng quan — duyệt / trả lại nhanh tại chỗ
 * khi có quyền `approve`.
 *
 * Không nhận `onRefresh`: `usePurchaseRequestAction` đã làm mất hiệu lực cả
 * nhánh `queryKeys.procurement`, mà số liệu trang này nằm đúng trong nhánh đó
 * (`['procurement', 'dashboard']`) nên bảng tự nạp lại. Gọi thêm `refetch` chỉ
 * tổ bắn hai lượt cùng một request.
 */
export function RecentPurchaseRequests({ rows }: RecentPurchaseRequestsProps) {
  const { can } = usePermission()
  const canApprove = can('purchase_request', 'approve')
  const isMobile = useIsMobile()

  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Chưa có yêu cầu mua hàng nào.
      </p>
    )
  }

  //  ⚠️ Ở khổ điện thoại dựng THẺ, không dựng bảng thu nhỏ. Bảng này rộng tự
  //  nhiên **687px** trong khung 308px (đo 12/09/2026 ở 390px): phần nhìn thấy
  //  chỉ tới giữa cột *Nội dung*, nên GIÁ TRỊ, TRẠNG THÁI và — nặng nhất — hai
  //  nút *Duyệt / Trả lại* nằm ngoài mép phải. Tức chức năng chính của khối này
  //  ("duyệt nhanh tại chỗ") biến mất trên điện thoại mà không có gì báo, người
  //  dùng phải đoán ra là kéo ngang được.
  //
  //  Dựng ĐÚNG MỘT nhánh (`useIsMobile`) chứ không hai khối `md:hidden` —
  //  `QuickActions` có hộp thoại xác nhận, để hai bản trong cây DOM là hai hộp
  //  thoại cùng nhãn và trình đọc màn hình đọc mỗi phiếu hai lượt.
  if (isMobile) {
    return (
      <ul className="divide-y">
        {rows.map((row) => (
          <RecentRequestCard key={row.id} row={row} canApprove={canApprove} />
        ))}
      </ul>
    )
  }

  return (
    <div className="overflow-x-auto">
      {/* QA 29/08: trước ép min-w-[850px] nên nằm trong thẻ 2/3 bề ngang là đẻ
          thanh cuộn ngang cắt cụt cột. Nay bộ phận gộp vào dòng người yêu cầu
          (đỡ hẳn một cột), chỉ giữ sàn cho màn hẹp, cột nội dung nhận phần co
          giãn (w-full + max-w-0 để truncate ăn trong table-cell). */}
      <Table className="min-w-[480px]">
        <TableHeader>
          <TableRow>
            <TableHead className="w-28">Mã phiếu</TableHead>
            <TableHead className="min-w-40">Người yêu cầu / Nội dung</TableHead>
            <TableHead className="w-24">Ngày</TableHead>
            <TableHead className="w-32 text-right">Giá trị</TableHead>
            <TableHead className="w-32">Trạng thái</TableHead>
            {canApprove && <TableHead className="w-28 text-center">Thao tác</TableHead>}
          </TableRow>
        </TableHeader>

        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.id}>
              <TableCell className="font-semibold whitespace-nowrap text-sky-600 dark:text-sky-400">
                {row.code}
              </TableCell>
              <TableCell className="w-full max-w-0">
                <span className="block truncate font-medium" title={row.department || undefined}>
                  {row.requester}
                  {row.department && (
                    <span className="font-normal text-muted-foreground"> · {row.department}</span>
                  )}
                </span>
                <span
                  className="block truncate text-xs text-muted-foreground"
                  title={row.description}
                >
                  {row.description || '—'}
                </span>
              </TableCell>
              <TableCell className="whitespace-nowrap">{formatDate(row.date) || '—'}</TableCell>
              <TableCell className="text-right font-medium whitespace-nowrap tabular-nums">
                {formatMoney(row.total)} đ
              </TableCell>
              <TableCell>
                <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />
              </TableCell>
              {canApprove && (
                <TableCell className="text-center">
                  {row.status === 'submitted' ? (
                    <QuickActions id={row.id} code={row.code} />
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

/**
 * Một yêu cầu mua ở khổ ĐIỆN THOẠI.
 *
 * ⚠️ **NỘI DUNG lên dòng đầu, mã phiếu tụt xuống dòng phụ** — cùng bài học với
 * `DocumentCard` / `ApprovalInboxCard` (CR-364/365). Mã phiếu xếp dọc thành một
 * cột `PYCDEMO0…` giống hệt nhau, không nói được phiếu nào là phiếu nào; thứ
 * phân biệt chúng là câu nội dung ("Mua thùng bù tồn kho quý 2").
 *
 * ⚠️ **Giá trị KHÔNG rút gọn.** Người duyệt bấm *Duyệt* dựa trên đúng con số
 * này, mà "1,2 tr" và "1.234.567 đ" là hai mức tin cậy khác nhau khi thứ theo
 * sau là một chữ ký.
 */
function RecentRequestCard({
  row,
  canApprove,
}: {
  row: RecentPurchaseRequest
  canApprove: boolean
}) {
  return (
    <li className="space-y-1.5 py-3 first:pt-0">
      <span className="line-clamp-2 font-medium text-foreground">{row.description || '—'}</span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 items-center gap-1 text-xs text-muted-foreground">
        <span className="shrink-0 font-semibold text-sky-600 dark:text-sky-400">{row.code}</span>
        <span className="truncate">
          <span aria-hidden="true">· </span>
          {row.requester}
          {row.department && ` · ${row.department}`}
        </span>
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />
        <span className="text-xs whitespace-nowrap text-muted-foreground">
          {formatDate(row.date) || '—'}
        </span>
        <span className="text-xs font-semibold whitespace-nowrap tabular-nums text-foreground">
          {formatMoney(row.total)} đ
        </span>

        {/*  Nút bám mép phải của CHÍNH hàng huy hiệu, không xuống một hàng
             riêng: hàng riêng cho hai nút biểu tượng làm mỗi phiếu cao thêm
             40px × 8 phiếu, mà chỗ trống bên phải huy hiệu thì đang bỏ không. */}
        {canApprove && row.status === 'submitted' && (
          <div className="ml-auto">
            <QuickActions id={row.id} code={row.code} />
          </div>
        )}
      </div>
    </li>
  )
}

/**
 * Hai nút thao tác của MỘT dòng. Tách thành component riêng vì
 * `usePurchaseRequestAction` nhận `id` lúc dựng hook — không gọi được trong
 * vòng lặp của bảng.
 *
 * Không tự bắn toast lỗi: `httpClient` đã toast mọi lời gọi không phải GET, tự
 * thêm nữa là người dùng thấy hai thông báo chồng nhau. Câu báo thành công do
 * chính hook lo, dùng chung với màn chi tiết.
 */
function QuickActions({ id, code }: { id: number; code: string }) {
  const runAction = usePurchaseRequestAction(id)
  const [askReturn, setAskReturn] = useState(false)

  return (
    <div className="flex items-center justify-center gap-1.5">
      <ConfirmIconButton
        icon={Check}
        title="Duyệt nhanh"
        confirmTitle={`Duyệt phiếu ${code}?`}
        confirmDescription="Phiếu chuyển sang Đã duyệt và đi tiếp sang bước điều phối."
        confirmLabel="Duyệt"
        disabled={runAction.isPending}
        onConfirm={() => runAction.mutate({ action: 'approve' })}
      />

      {/* Nút này gọi `/reject`, mà backend đặt phiếu về `rejected` = "Bị trả
          lại" (người yêu cầu sửa rồi gửi lại được), KHÔNG phải "Đã từ chối"
          (`cancelled`, khóa hẳn). Nhãn phải nói đúng việc nó làm. */}
      <Button
        size="icon-sm"
        variant="ghost"
        title="Trả lại để sửa"
        aria-label="Trả lại để sửa"
        disabled={runAction.isPending}
        className="text-destructive hover:text-destructive"
        onClick={() => setAskReturn(true)}
      >
        <CornerUpLeft />
      </Button>

      <ReasonConfirmDialog
        open={askReturn}
        onOpenChange={setAskReturn}
        title={`Trả lại phiếu ${code}`}
        description="Phiếu chuyển sang Bị trả lại để người yêu cầu sửa và gửi duyệt lại. Lý do được gửi kèm thông báo cho họ."
        placeholder="Vì sao phiếu chưa duyệt được?"
        confirmText="Trả lại"
        destructive
        pending={runAction.isPending}
        onConfirm={(reason) => {
          setAskReturn(false)
          runAction.mutate({ action: 'reject', reason })
        }}
      />
    </div>
  )
}
