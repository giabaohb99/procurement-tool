import { ArrowLeft } from 'lucide-react'
import { Fragment, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { HeaderActionsPopover } from '@/shared/ui/header-actions-popover'
import { cn } from '@/shared/utils/cn'

/**
 * Một nút của dải đầu trang khi xếp theo THỨ TỰ BẢN V1 (duoc-CR-737).
 *
 * `group: 'utility'` = nhóm tiện ích bên trái vạch ngăn (In · Nhân bản · Xóa…);
 * mặc định `'workflow'` = các nút đi theo bước quy trình, bên phải vạch ngăn.
 * `primary` = nút nền đặc: khổ hẹp vẫn để ngoài, còn lại gom vào `⋯`.
 */
export interface HeaderAction {
  key: string
  node: ReactNode
  primary?: boolean
  group?: 'utility' | 'workflow'
}

/** Cho phép khai mảng kèm điều kiện: `[cond && {...}]` — giá trị rỗng bị bỏ. */
export type HeaderActionList = ReadonlyArray<HeaderAction | false | null | undefined>

export interface DetailPageHeaderProps {
  /** Đường về danh sách của phân hệ. */
  backTo: string
  /** Nhãn đọc màn hình cho nút mũi tên — nút chỉ có biểu tượng. */
  backLabel: string
  title: string
  /** Huy hiệu trạng thái, cờ *Đơn gấp*… — thứ DUY NHẤT được phép xuống dòng. */
  badges?: ReactNode
  /** Nút nền đặc: việc người mở trang đang định làm. LUÔN ở ngoài. */
  primaryActions?: ReactNode
  /** Nút viền: khổ rộng bày thẳng, khổ hẹp gom vào `⋯`. */
  secondaryActions?: ReactNode
  /**
   * Xếp nút theo ĐÚNG THỨ TỰ BẢN V1 (duoc-CR-737): nhóm tiện ích · vạch ngăn ·
   * nút quy trình, nút đặc và nút viền xen nhau theo bước. Người dùng dời từ v1
   * sang v2 tìm nút ở đúng chỗ cũ. Khai `actions` thì bỏ qua `primaryActions` /
   * `secondaryActions`. Khổ hẹp: nút `primary` ở ngoài, còn lại vào `⋯` (giữ thứ tự).
   */
  actions?: HeaderActionList
  /**
   * Ghim dải đầu trang ở khổ hẹp. Dùng cho màn dài mà lệnh hay phải với tới
   * giữa chừng (Phiếu khảo sát). Mặc định tắt: ghim là ăn vĩnh viễn ~60px của
   * màn 844px, không đáng cho màn chỉ đọc.
   */
  sticky?: boolean
  className?: string
}

/**
 * Dải đầu của TRANG CHI TIẾT chứng từ: mũi tên về · mã phiếu · huy hiệu · nút.
 *
 * Bốn trang (YCMH · YCBG · ĐMH · Phiếu khảo sát) từng chép tay cùng một khối
 * này, và mỗi lần sửa luật khổ hẹp lại phải nhớ sửa đủ bốn chỗ — gom về đây.
 *
 * ⚠️ **Cụm nút ở LẠI hàng đầu, huy hiệu mới là thứ được phép xuống dòng.** Để
 * tiêu đề + huy hiệu + nút chung một hàng `flex-wrap` thì SỐ HUY HIỆU quyết định
 * nút rơi đi đâu — vị trí nút *Lưu* đổi theo DỮ LIỆU, người dùng không đoán
 * được. Ô tiêu đề là một khối `flex-wrap` riêng nên huy hiệu tự tụt xuống dòng
 * hai bên trong nó, còn cụm nút không bị đẩy đi đâu cả.
 *
 * ⚠️ **KHÔNG `min-w-0` ở ô tiêu đề.** `min-w-0` cho nó co về 0, nên khi cụm nút
 * rộng trình duyệt chọn CO TIÊU ĐỀ thay vì đẩy cụm nút xuống hàng — mã phiếu bị
 * cắt cụt ngay giữa chữ. Để min-content của mã phiếu được tôn trọng thì lớp
 * ngoài `flex-wrap` mới có cớ xuống dòng, và mã phiếu luôn đọc đủ.
 *
 * ⚠️ **Ba thứ bóp lại ở khổ hẹp, và cả ba đều cần** để cụm nút còn ở được hàng
 * đầu trên máy 390px (khung nội dung ~358px):
 *   · khoảng cách `gap-2` thay vì `gap-3` — ba khe, tiết kiệm 12px;
 *   · tiêu đề `text-lg` thay vì `text-xl` — mã phiếu 11 ký tự hẹp đi ~17px;
 *   · **nhãn nút chính phải NGẮN** (xem ghi chú ở nơi gọi).
 * Thiếu một vế thì cả cụm nút rớt xuống hàng riêng, và vì nó `ml-auto` nên nó
 * nằm nép phải, chừa một mảng trống dài bên trái — đúng thứ khách gọi là "nằm
 * trên dưới" ngày 14/09/2026.
 *
 * ⚠️ **Nhóm phụ dựng MỘT LẦN, `useIsMobile` chỉ chọn khung BỌC** — đừng dựng
 * hai bản rồi ẩn một bằng CSS. Nút ở đây thường mang hộp thoại và mutation riêng
 * (`DeleteConfirmButton`, hộp nhập lý do): bản bị ẩn vẫn gắn kết, vẫn giữ state,
 * vẫn bắn được request.
 */
export function DetailPageHeader({
  backTo,
  backLabel,
  title,
  badges,
  primaryActions,
  secondaryActions,
  actions,
  sticky = false,
  className,
}: DetailPageHeaderProps) {
  const isMobile = useIsMobile()

  return (
    <div
      className={cn(
        'mb-4 flex flex-wrap items-start gap-2 md:gap-3',
        //  Khổ hẹp bóp đệm dọc lại: dải xuống hai hàng ở đó, để nguyên đệm của
        //  màn rộng là mất ~117px trên tổng 844px vĩnh viễn.
        sticky &&
          'max-md:sticky max-md:top-0 max-md:z-20 max-md:-mx-4 max-md:-mt-4 max-md:mb-0 max-md:border-b max-md:bg-canvas max-md:px-4 max-md:pt-2 max-md:pb-3',
        className,
      )}
    >
      <Button
        variant="outline"
        size="icon"
        asChild
        className="shrink-0"
        aria-label={backLabel}
      >
        <Link to={backTo}>
          <ArrowLeft />
        </Link>
      </Button>

      <div className="flex flex-1 flex-wrap items-center gap-x-2 gap-y-1.5 md:gap-x-3">
        <h1 className="text-lg font-semibold tracking-tight text-navy md:text-xl dark:text-foreground">
          {title}
        </h1>
        {badges}
      </div>

      <div className="ml-auto flex shrink-0 flex-wrap items-center justify-end gap-2">
        {actions ? (
          <OrderedHeaderActions actions={actions} isMobile={isMobile} />
        ) : (
          <>
            {primaryActions}
            {secondaryActions &&
              (isMobile ? (
                <HeaderActionsPopover>{secondaryActions}</HeaderActionsPopover>
              ) : (
                secondaryActions
              ))}
          </>
        )}
      </div>
    </div>
  )
}

/**
 * Cụm nút xếp theo thứ tự bản v1. Mỗi nút dựng MỘT LẦN — `isMobile` chỉ chọn
 * nó đứng ngoài hay trong `⋯` (xem ghi chú "Nhóm phụ dựng MỘT LẦN" ở trên).
 */
function OrderedHeaderActions({
  actions,
  isMobile,
}: {
  actions: HeaderActionList
  isMobile: boolean
}) {
  const items = actions.filter((item): item is HeaderAction => Boolean(item))
  const utility = items.filter((item) => item.group === 'utility')
  const workflow = items.filter((item) => item.group !== 'utility')

  if (isMobile) {
    const outside = items.filter((item) => item.primary)
    const menu = [...utility, ...workflow].filter((item) => !item.primary)
    return (
      <>
        {outside.map((item) => (
          <Fragment key={item.key}>{item.node}</Fragment>
        ))}
        {menu.length > 0 && (
          <HeaderActionsPopover>
            {menu.map((item) => (
              <Fragment key={item.key}>{item.node}</Fragment>
            ))}
          </HeaderActionsPopover>
        )}
      </>
    )
  }

  return (
    <>
      {utility.map((item) => (
        <Fragment key={item.key}>{item.node}</Fragment>
      ))}
      {utility.length > 0 && workflow.length > 0 && (
        <span aria-hidden className="mx-1 h-6 w-px self-center bg-border" data-testid="header-actions-divider" />
      )}
      {workflow.map((item) => (
        <Fragment key={item.key}>{item.node}</Fragment>
      ))}
    </>
  )
}

/**
 * Nhãn nút đổi theo khổ màn — bản DÀI ở khổ rộng, bản NGẮN ở khổ hẹp.
 *
 * ⚠️ Ở đây đổi bằng CSS được (khác `SearchField`, nơi nhãn là thuộc tính
 * `placeholder` chứ không phải nút DOM): cả hai bản đều nằm trong cây, chỉ một
 * bản được vẽ. Đừng cắt bằng bề rộng ô — trình duyệt xén giữa chừng và ra
 * "Tạo yêu cầu m…", tức mất đúng phần cuối.
 *
 * ⚠️ **Bản ngắn phải là từ viết tắt NGƯỜI DÙNG ĐANG DÙNG** (YCMH · YCBG · ĐMH —
 * xem `doc/`), không phải chữ tự nghĩ ra cho vừa chỗ.
 */
export function ResponsiveLabel({ short, long }: { short: string; long: string }) {
  return (
    <>
      <span className="md:hidden">{short}</span>
      <span className="max-md:hidden">{long}</span>
    </>
  )
}
