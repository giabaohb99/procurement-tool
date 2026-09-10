import {
  ArrowUpDown,
  Check,
  ChevronDown,
  Diamond,
  Funnel,
  Plus,
  Rows3,
  Search,
  SlidersHorizontal,
  X,
  type LucideIcon,
} from 'lucide-react'
import { useState } from 'react'

import { ConditionalFilter } from '@/shared/conditional-filter'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { CardFieldsMenu } from './card-fields-menu'
import type { WorkLabelField } from '../types/work'
import type { CardFields, WorkSort } from '../types/view-options'

interface WorkToolbarProps {
  listId: number
  sort: WorkSort
  /**
   * Bộ tiêu chí sắp xếp — do TRANG dựng, vì mỗi dự án còn có thêm một dòng cho
   * mỗi trường tùy biến (độ ưu tiên nay là một trong số đó).
   */
  sortOptions: { value: WorkSort; label: string }[]
  onSortChange: (value: WorkSort) => void
  keyword: string
  onKeywordChange: (value: string) => void
  fields: CardFields
  onFieldsChange: (fields: CardFields) => void
  /** Bộ nhãn tùy biến của dự án — menu «Tùy chỉnh» lấy tên trường từ đây. */
  labelFields: WorkLabelField[]
  /** Mở màn Thiết lập để khai thêm nhãn; vắng = không đủ quyền. */
  onAddField?: () => void
  canEdit: boolean
  /** ADMIN trở lên: được sửa tag / trường tùy biến ngay trong menu «Tùy chỉnh». */
  canManage: boolean
  onNewTask: () => void
  /**
   * Thêm CỘT MỐC (B-14) — nằm trong mũi tên cạnh «Việc mới». Vắng = không đủ
   * quyền sửa. Tách khỏi «Việc mới» vì mốc mang ngày khác hẳn (chỉ một mốc) và
   * hiện thành hình thoi trên Gantt.
   */
  onNewMilestone?: () => void
  /** Thêm cột — cũng nằm trong mũi tên ấy. Vắng = không đủ quyền quản trị. */
  onAddSection?: () => void
}

/**
 * Thanh công cụ khung nhìn (D-07) — clone hàng nút của Lark.
 *
 * Hình dáng bám đúng bản gốc: **một nút tách đôi** «Việc mới ▾» có viền, rồi
 * một dải nút CHỮ KHÔNG VIỀN (lọc · sắp xếp · tùy chỉnh) và ô tìm thu gọn ở mép
 * phải. Trước đây mỗi thứ là một ô `Select` viền kín rộng cố định, nên nhãn dài
 * bị cắt cụt ngay trên thanh (`Sắp xếp: Tay (kéo th…`).
 *
 * Mọi thứ ở đây là **hiển thị**: lọc/sắp ngay tại trình duyệt trên payload bảng
 * đã tải — một list vài trăm việc thì đi vòng máy chủ chỉ tốn thêm một nhịp chờ.
 *
 * ⚠️ Nút «lát cắt nhanh» ĐÃ BỎ (Tất cả việc / Việc của tôi…): mọi lát cắt đó nay
 * khai bằng bộ lọc điều kiện. Còn thiếu **«Gom nhóm»** (§3.5) — chưa dựng nút
 * chết ở đây: bấm vào không làm gì còn tệ hơn là thiếu hẳn.
 */
export function WorkToolbar({
  listId,
  sort,
  sortOptions,
  onSortChange,
  keyword,
  onKeywordChange,
  fields,
  onFieldsChange,
  labelFields,
  onAddField,
  canEdit,
  canManage,
  onNewTask,
  onNewMilestone,
  onAddSection,
}: WorkToolbarProps) {
  //  Mũi tên chỉ mọc ra khi có ÍT NHẤT một mục khác «Việc mới» — một menu chỉ
  //  chứa đúng cái nút bên cạnh đã làm là menu thừa.
  const hasMenu = Boolean(onNewMilestone || onAddSection)

  const isMobile = useIsMobile()
  const [searching, setSearching] = useState(false)
  //  Còn từ khóa thì ô tìm phải ở nguyên đó dù đã rời ô — ô biến mất trong khi
  //  bảng vẫn đang lọc thì người dùng nhìn bảng thiếu việc và không biết vì sao.
  const searchOpen = searching || keyword !== ''

  const searchField = (
    <ToolbarSearch
      keyword={keyword}
      onChange={onKeywordChange}
      open={searchOpen}
      onOpenChange={setSearching}
      fullWidth={isMobile && searchOpen}
    />
  )

  //  ⚠️ Khổ hẹp, đang tìm: ô tìm chiếm TRỌN hàng và các nút kia tạm nhường chỗ.
  //  Ô rộng cố định 224px không nhét vừa phần thừa của hàng (chỉ còn ~94px), nên
  //  bản trước nó rơi xuống một hàng thứ hai — bấm cái kính lúp xong cả thanh
  //  công cụ giật xuống, mà ô vừa hiện ra lại nằm chỗ khác với chỗ vừa bấm. Ép
  //  nó co vào 94px cũng không xong: gõ được đâu chừng mười ký tự rồi chữ trôi.
  //  Tìm kiếm là một CHẾ ĐỘ, không phải một nút thứ sáu — nhường cả hàng cho nó
  //  thì hàng không đổi chiều cao, không đổi chỗ, và ô đủ rộng để đọc lại câu
  //  mình vừa gõ. Rời ô lúc chưa gõ gì là mọi thứ trở về như cũ.
  if (isMobile && searchOpen) {
    return <div className="flex items-center gap-1">{searchField}</div>
  }

  return (
    <div className="flex flex-wrap items-center gap-1">
      {canEdit && (
        //  Nút tách đôi: nửa trái làm việc chính, nửa phải mở menu. Viền vẽ ở
        //  KHUNG NGOÀI chứ không ở từng nút, không thì chỗ nối thành hai nét.
        <div className="inline-flex items-center rounded-md border bg-background shadow-xs dark:border-input dark:bg-input/30">
          <Button
            variant="ghost"
            size="sm"
            className={cn('px-2.5', hasMenu && 'rounded-r-none')}
            onClick={onNewTask}
          >
            <Plus className="size-4" />
            Việc mới
          </Button>
          {hasMenu && (
            <>
              <span aria-hidden className="h-5 w-px bg-border" />
              <DropdownMenu>
                <IconTooltip label="Thêm mục khác">
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="rounded-l-none"
                      aria-label="Thêm mục khác"
                    >
                      <ChevronDown className="size-4" />
                    </Button>
                  </DropdownMenuTrigger>
                </IconTooltip>
                <DropdownMenuContent align="start">
                  <DropdownMenuItem onClick={onNewTask}>
                    <Plus className="size-4" />
                    Việc mới
                  </DropdownMenuItem>
                  {onNewMilestone && (
                    <DropdownMenuItem onClick={onNewMilestone}>
                      <Diamond className="size-4" />
                      Cột mốc mới
                    </DropdownMenuItem>
                  )}
                  {onAddSection && (
                    <DropdownMenuItem onClick={onAddSection}>
                      <Rows3 className="size-4" />
                      Cột mới
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          )}
        </div>
      )}

      {canEdit && <span aria-hidden className="mx-1.5 h-5 w-px bg-border" />}

      {/*  Nút «Lọc» của bộ lọc điều kiện dùng chung. Lọc chạy tại trình duyệt
          trên payload bảng đã tải — xem `applyTaskConditions`.

          ⚠️ Khổ hẹp: ba nút này rút về CÒN BIỂU TƯỢNG. Đo ở 390px thì cả thanh
          rộng ~550px trên 358px dùng được nên nó rớt xuống hai hàng, mà hàng
          thứ hai ăn thêm 40px chiều cao của một màn vốn đã phải cuộn. Bỏ ba
          nhãn («Bộ lọc» 83px · «Sắp xếp: …» 188px · «Tùy chỉnh» 106px) là vừa
          một hàng. Giữ nhãn cho «Việc mới» vì đó là hành động chính, và giữ
          huy hiệu đếm điều kiện vì nó là thứ nói bảng ĐANG BỊ LỌC — mất nó thì
          người dùng nhìn bảng thiếu việc mà không hiểu vì sao. */}
      <ConditionalFilter
        variant="ghost"
        icon={Funnel}
        labelClassName="max-md:hidden"
        className="text-muted-foreground hover:text-foreground max-md:px-2"
      />

      <ToolbarMenu
        icon={ArrowUpDown}
        srLabel="Sắp xếp"
        prefix="Sắp xếp: "
        value={sort}
        options={sortOptions}
        onChange={onSortChange}
      />

      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Tùy chỉnh trường hiện trên thẻ"
            className="text-muted-foreground hover:text-foreground max-md:px-2"
          >
            <SlidersHorizontal className="size-4" />
            <span className="max-md:hidden">Tùy chỉnh</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-80">
          <CardFieldsMenu
            listId={listId}
            fields={fields}
            labelFields={labelFields}
            onChange={onFieldsChange}
            onAddField={onAddField}
            canManage={canManage}
          />
        </PopoverContent>
      </Popover>

      {searchField}
    </div>
  )
}

/**
 * Ô tìm THU GỌN thành một biểu tượng, bung ra khi bấm — đúng khuôn Lark.
 *
 * Không để ô nhập mở sẵn: sáu nút kia đã chiếm 740px, thêm một ô 224px là thanh
 * công cụ tràn xuống hàng thứ hai ngay ở màn hình 1280 có mở menu trái.
 * Thu lại khi rời ô, nhưng CHỈ khi chưa gõ gì — còn từ khóa mà ô biến mất thì
 * người dùng nhìn bảng thiếu việc và không biết vì sao (chốt mở/đóng nằm ở
 * `WorkToolbar`, xem `searchOpen`).
 *
 * ⚠️ **Ô phải CÓ VIỀN.** Bản trước khai `border-transparent bg-transparent
 * shadow-none`, viền chỉ hiện khi rê chuột: trên nền canvas xam xám nó gần như
 * tàng hình, và trên máy cảm ứng thì không có nhịp «rê chuột» nào cả — bấm kính
 * lúp xong người dùng thấy con trỏ nháy giữa khoảng không, không rõ gõ vào đâu
 * và vùng gõ rộng tới đâu. Ô nhập là chỗ NHẬN thao tác, nó phải tự nói ra mình
 * ở đâu chứ không đợi được hỏi.
 */
function ToolbarSearch({
  keyword,
  onChange,
  open,
  onOpenChange,
  fullWidth,
}: {
  keyword: string
  onChange: (value: string) => void
  open: boolean
  onOpenChange: (value: boolean) => void
  /** Nở hết hàng — khổ hẹp, xem ghi chú «chế độ tìm» ở `WorkToolbar`. */
  fullWidth?: boolean
}) {
  if (!open) {
    return (
      <IconTooltip label="Tìm trong danh sách">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Tìm trong danh sách"
          className="ml-auto text-muted-foreground hover:text-foreground"
          onClick={() => onOpenChange(true)}
        >
          <Search className="size-4" />
        </Button>
      </IconTooltip>
    )
  }

  return (
    <div className={cn('relative', fullWidth ? 'w-full' : 'ml-auto')}>
      <Search className="absolute top-1/2 left-2 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        autoFocus
        value={keyword}
        onChange={(su) => onChange(su.target.value)}
        onBlur={() => onOpenChange(false)}
        placeholder="Tìm trong danh sách"
        aria-label="Tìm trong danh sách"
        className={cn('h-8 pr-8 pl-8', fullWidth ? 'w-full' : 'w-56')}
      />
      {/*  ⚠️ Nút X LUÔN có, kể cả khi chưa gõ gì, và nó ĐÓNG ô chứ không chỉ xóa
           chữ. Đường đóng duy nhất trước đây là rời ô — trên máy cảm ứng thì
           «rời ô» nghĩa là chạm vào bảng phía dưới, mà mọi thứ dưới đó đều kéo
           thả được: định thoát tìm kiếm thì nhấc nhầm một cái thẻ việc. Xóa
           chữ và đóng ô gộp làm một vì tách ra là tự mâu thuẫn: còn từ khóa thì
           ô lại mở ra ngay (xem `searchOpen`), mà đóng ô trong khi bảng vẫn
           đang lọc thì người dùng nhìn bảng thiếu việc và không hiểu vì sao. */}
      <IconTooltip label="Đóng ô tìm">
        <button
          type="button"
          aria-label="Đóng ô tìm"
          //  Chặn `blur` ở `onMouseDown` (nếu không thì ô đóng trước, cú bấm rơi
          //  vào chỗ trống), nhưng việc thật làm ở `onClick` — bàn phím chỉ bắn
          //  ra `click`, đặt hết vào `onMouseDown` là nút chết với phím Enter.
          onMouseDown={(su) => su.preventDefault()}
          onClick={() => {
            onChange('')
            onOpenChange(false)
          }}
          className="absolute top-1/2 right-1.5 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <X className="size-3.5" />
        </button>
      </IconTooltip>
    </div>
  )
}

interface ToolbarMenuProps<T extends string> {
  icon: LucideIcon
  /** Tên trường — chỉ cho trình đọc màn hình, vì nút hiện GIÁ TRỊ đang chọn. */
  srLabel: string
  /** Chữ dẫn trước giá trị trên nút, ví dụ «Sắp xếp: ». */
  prefix?: string
  value: T
  options: readonly { value: T; label: string }[]
  onChange: (value: T) => void
}

/**
 * Nút chữ không viền mở menu một-lựa-chọn — khuôn `Sort by: Custom` của Lark.
 *
 * Dùng `DropdownMenu` chứ không phải `Select`: nút phải hiện đúng một dòng chữ
 * gọn (không mũi tên, không khung), mà `Select` thì luôn kèm mũi tên và cần
 * `SelectValue` làm mốc canh khung thả xuống.
 */
function ToolbarMenu<T extends string>({
  icon: Icon,
  srLabel,
  prefix,
  value,
  options,
  onChange,
}: ToolbarMenuProps<T>) {
  const current = options.find((o) => o.value === value)
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          //  Nút chỉ hiện GIÁ TRỊ đang chọn («Tất cả việc (chưa xong)»), nên tên
          //  cho trình đọc màn hình phải kèm luôn tên trường — không thì nghe
          //  xong vẫn không biết đó là lát cắt hay bộ lọc nào.
          aria-label={`${srLabel}: ${current?.label ?? ''}`}
          className="text-muted-foreground hover:text-foreground max-md:px-2"
        >
          <Icon className="size-4" />
          {/*  Khổ hẹp giấu cả tiêu chí đang chọn — nó là nhãn dài nhất thanh
               (188px). Giá trị không mất: mở menu ra là mục đang chọn có dấu
               tích và tô màu nhấn. */}
          <span className="max-md:hidden">
            {prefix}
            {current?.label ?? ''}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {/*  Khuôn menu của Lark: mục đang chọn tô màu nhấn và có DẤU TÍCH ở mép
            PHẢI. Vì thế không dùng `DropdownMenuRadioItem` — chấm chỉ báo của nó
            gắn cứng ở mép trái. Vai trò `menuitemradio` vẫn khai đủ để trình đọc
            màn hình đọc ra "đang chọn". */}
        {options.map((o) => (
          <DropdownMenuItem
            key={o.value}
            role="menuitemradio"
            aria-checked={o.value === value}
            onSelect={() => onChange(o.value)}
            className={cn(o.value === value && 'text-primary focus:text-primary')}
          >
            {o.label}
            {o.value === value && <Check className="ml-auto size-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
