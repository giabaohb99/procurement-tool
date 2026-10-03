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
 */
export function EmployeeWorkHistoryViewToggle({ value, onChange }: EmployeeWorkHistoryViewToggleProps) {
  return (
    <ToggleGroup
      type="single"
      variant="outline"
      size="sm"
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
