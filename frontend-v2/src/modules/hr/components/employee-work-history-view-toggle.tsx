import { History, Table2 } from 'lucide-react'

import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'

/** Hai cách xem của mỗi khu — nơi gọi lưu giá trị vào URL (`useUrlParamState`). */
export type WorkHistoryViewMode = 'table' | 'timeline'

interface EmployeeWorkHistoryViewToggleProps {
  value: WorkHistoryViewMode
  onChange: (next: WorkHistoryViewMode) => void
}

/**
 * Nút chuyển «Bảng | Dòng thời gian» — dùng CHUNG cho cả hai khu («Quyết định
 * bổ nhiệm» và «Quá trình công tác») ở tab hồ sơ VÀ ở thẻ Trang cá nhân `/me`
 * (đại ca chốt 03/10/2026). Không tự giữ state — nơi gọi lưu lựa chọn vào URL
 * search param riêng của từng khu (`whView`/`decView`) để tải lại trang hay
 * gửi link vẫn giữ đúng cách xem.
 *
 * `ToggleGroup type="single"` của Radix vẽ mỗi lựa chọn bằng `role="radio"`
 * (khớp `report-compare-toggle.tsx`) — `next && onChange(...)` chặn trường hợp
 * Radix gửi chuỗi rỗng lúc bấm lại đúng lựa chọn đang chọn (không cho bỏ chọn
 * hết, luôn phải còn một cách xem đang mở).
 *
 * Size mặc định `"default"` (h-9) — CỐ Ý khớp chiều cao nút outline đứng cạnh
 * nó trên cùng một hàng (Tải lại `size="icon"`, Cột không khai size, cả hai
 * đều h-9); từng để `size="sm"` (h-8) lúc toggle còn đứng hàng riêng, thấp hơn
 * 4px so với cụm nút bên cạnh sau khi gộp một hàng (đại ca chê, 03/10/2026).
 */
export function EmployeeWorkHistoryViewToggle({ value, onChange }: EmployeeWorkHistoryViewToggleProps) {
  return (
    <ToggleGroup
      type="single"
      variant="outline"
      value={value}
      onValueChange={(next) => next && onChange(next as WorkHistoryViewMode)}
    >
      <ToggleGroupItem value="table">
        <Table2 className="size-4" />
        Bảng
      </ToggleGroupItem>
      <ToggleGroupItem value="timeline">
        <History className="size-4" />
        Dòng thời gian
      </ToggleGroupItem>
    </ToggleGroup>
  )
}
