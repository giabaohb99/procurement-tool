import { useMemo } from 'react'

import type { DataTableColumn } from '@/shared/data-table'
import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { Switch } from '@/shared/ui/switch'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'
import { nameInitials } from '@/shared/utils/name-initials'
import { CompanyAvatarGroup } from '../components/company-avatar-group'
import { ClerkStatusBadge } from '../components/status-pill'
import type { SealClerkGroup } from '../types/seal-clerk'
import { shortCompanyName } from '../utils/short-company-name'

interface UseSealClerkColumnsOptions {
  canManage: boolean
  /** Đang gửi lệnh bật/tắt văn thư tổng — khóa công tắc lại cho khỏi bấm chồng. */
  isPending: boolean
  onToggleHead: (row: SealClerkGroup, isHead: boolean) => void
}

/**
 * Cột của bảng Phân công văn thư.
 *
 * Tách khỏi trang vì phần khai cột chiếm quá nửa tệp; trang chỉ còn phần gọi API,
 * lọc và xếp khung.
 *
 * KHÔNG có cột "Thao tác" (bỏ 22/09/2026): cả hàng đã bấm được để mở chi tiết,
 * nên nút đó chỉ lặp lại một việc đã có — mà lại là cột hẹp nhất bảng nên chữ
 * "Chi tiết" cụt mất biểu tượng.
 */
export function useSealClerkColumns({
  canManage,
  isPending,
  onToggleHead,
}: UseSealClerkColumnsOptions) {
  return useMemo<DataTableColumn<SealClerkGroup>[]>(
    () => [
      {
        key: 'employee',
        header: 'Văn thư đóng dấu',
        minWidth: 260,
        sortable: true,
        hideable: false,
        cell: (r) => (
          <div className="flex items-center gap-3 py-1">
            <Avatar
              size="sm"
              className="size-8 shrink-0 border border-border/70 bg-primary/10 shadow-2xs"
            >
              <AvatarFallback className="text-xs font-bold text-primary">
                {nameInitials(r.employee_name || '')}
              </AvatarFallback>
            </Avatar>

            <div className="min-w-0">
              <div className="flex min-w-0 items-center gap-2">
                <span className="truncate text-sm font-semibold text-navy dark:text-foreground">
                  {r.employee_name || `#${r.employee_id}`}
                </span>
                {/*  `shrink-0`: không có nó thì huy hiệu bị ô bóp lại và cụt đuôi
                    ("Văn thư tổn…") — đúng lỗi thấy ở dòng thứ ba bản cũ. */}
                {r.is_head && (
                  <Badge
                    variant="outline"
                    className="shrink-0 border-indigo-200 bg-indigo-50 text-[10px] text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/60 dark:text-indigo-300"
                  >
                    Văn thư tổng
                  </Badge>
                )}
              </div>
              {r.employee_code && (
                <span className="text-[11px] text-muted-foreground">Mã: {r.employee_code}</span>
              )}
            </div>
          </div>
        ),
      },
      {
        //  ⚠️ Cột này khai `width` CỐ ĐỊNH và hẹp. Bảng `table-fixed` + `w-full`
        //  chia phần dôi ra cho những cột KHÔNG khai bề rộng, nên chỉ cần hai
        //  cột chữ (văn thư · công ty) để trống `width` là chúng nuốt hết chỗ
        //  thừa — còn cột chỉ chứa một công tắc 36px thì không phình lên thành
        //  một khoảng trắng giữa bảng như bản trước.
        key: 'is_head',
        header: 'Đa pháp nhân',
        width: 130,
        align: 'center',
        cell: (r) => (
          //  Ô có nút bấm thì phải chặn nổi bọt, không thì mỗi lần gạt công tắc
          //  là `onRowClick` mở luôn trang chi tiết.
          <div className="flex justify-center py-0.5" onClick={(e) => e.stopPropagation()}>
            <Tooltip disableHoverableContent>
              <TooltipTrigger asChild>
                <div>
                  <Switch
                    checked={r.is_head}
                    disabled={!canManage || isPending}
                    aria-label={`Quyền đa pháp nhân của ${r.employee_name || `#${r.employee_id}`}`}
                    onCheckedChange={(checked) => onToggleHead(r, checked)}
                  />
                </div>
              </TooltipTrigger>
              {/*  Chữ trạng thái cạnh công tắc đã BỎ: cùng một sự thật vốn đã
                  nói ba lần trên một hàng (huy hiệu ở cột tên · công tắc bật/tắt
                  · chữ "Đa pháp nhân"). Giữ lại lời giải thích ở chú giải, nơi
                  nói được ý nghĩa nghiệp vụ chứ không chỉ lặp tên cột. */}
              <TooltipContent side="top" className="max-w-xs text-xs">
                {r.is_head
                  ? 'Đang bật: Được phụ trách đóng dấu các phiếu yêu cầu nhiều công ty.'
                  : 'Đang tắt: Chỉ phụ trách đóng dấu các phiếu thuộc công ty chỉ định.'}
              </TooltipContent>
            </Tooltip>
          </div>
        ),
      },
      {
        //  ⚠️ `wrap` để tên công ty XUỐNG DÒNG cho đủ. Đây là cột người ta mở
        //  trang này để xem, mà tên pháp nhân Việt Nam dài 40-60 ký tự và ba cái
        //  nối nhau thì cắt bằng "…" là mất đúng phần phân biệt ("CÔNG TY TNHH
        //  XUẤT N…" — nhập khẩu gì thì chịu).
        //
        //  ⚠️ Kèm `shortCompanyName` chứ không bày tên đầy đủ: để nguyên thì ba
        //  pháp nhân chiếm NĂM dòng và bảng 5 văn thư không còn lọt một màn —
        //  đổi lỗi cắt chữ lấy lỗi phình hàng. Tiền tố "CÔNG TY TNHH…" lặp ở
        //  mọi dòng nên không phân biệt gì; tên đầy đủ vẫn còn trong chú giải
        //  khi rê vào ảnh đại diện.
        key: 'companies',
        header: 'Công ty phụ trách',
        minWidth: 320,
        wrap: true,
        cell: (r) => {
          if (r.companies.length === 0) return <span className="text-muted-foreground">—</span>
          return (
            <div className="flex min-w-0 items-start gap-2.5 py-1.5">
              <div className="shrink-0 pt-0.5">
                <CompanyAvatarGroup
                  companies={r.companies}
                  maxVisible={4}
                  showNameWhenSingle={false}
                  //  Tên công ty đã bày ngay bên cạnh nên "(n công ty)" chỉ chen
                  //  vào giữa; số lượng đọc được từ chính danh sách.
                  showCount={false}
                />
              </div>
              {/*  KHÔNG gắn `truncate` ở đây — class của ô con thắng lớp bọc của
                  bảng, gắn vào là `wrap` thành vô hiệu (docs/ui/table.md). */}
              <span className="min-w-0 text-xs leading-relaxed text-muted-foreground">
                {r.companies.map((c) => shortCompanyName(c.name)).join(' · ')}
              </span>
            </div>
          )
        },
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 140,
        align: 'center',
        cell: (r) => <ClerkStatusBadge status={r.status} label={r.status_label ?? undefined} />,
      },
    ],
    [canManage, isPending, onToggleHead],
  )
}
