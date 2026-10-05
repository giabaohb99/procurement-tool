// Cụm ô tìm + bốn ô chọn của mục «Thuốc BVTV» — tách khỏi `customs-pesticide-tab.tsx` (01/10/2026)
// để tệp đó không vượt 200 dòng khi thêm nút «Xuất Excel». Thuần hiển thị: nhận giá trị/hàm đặt
// giá trị từ trang cha, không tự giữ state hay gọi API.
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import type { CustomsPesticideOptions } from '../../types/customs-pesticide'
import { ALL_PESTICIDE_OPTIONS, BANNED_ONLY, formatBannedFilterLabel } from '../../utils/customs-pesticide'
import { toSentenceCaseIfShouting } from '../../utils/customs-pesticide-display'

interface CustomsPesticideFilterControlsProps {
  keyword: string
  onKeywordChange: (value: string) => void
  status: string
  onStatusChange: (value: string) => void
  pestGroup: string
  onPestGroupChange: (value: string) => void
  sector: string
  onSectorChange: (value: string) => void
  banned: string
  onBannedChange: (value: string) => void
  options: CustomsPesticideOptions | undefined
}

export function CustomsPesticideFilterControls({
  keyword,
  onKeywordChange,
  status,
  onStatusChange,
  pestGroup,
  onPestGroupChange,
  sector,
  onSectorChange,
  banned,
  onBannedChange,
  options,
}: CustomsPesticideFilterControlsProps) {
  return (
    <>
      <SearchField
        value={keyword}
        onChange={onKeywordChange}
        placeholder="Tên thuốc, hoạt chất, công ty, số đăng ký…"
        placeholderShort="Tên thuốc, hoạt chất…"
        aria-label="Tìm thuốc BVTV"
        className="w-full max-w-xs"
      />
      <Select value={status} onValueChange={onStatusChange}>
        <SelectTrigger className="w-44 max-md:w-full" aria-label="Lọc theo tình trạng">
          <SelectValue placeholder="Tình trạng" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_PESTICIDE_OPTIONS}>Tất cả tình trạng</SelectItem>
          {(options?.statuses ?? []).map((item) => (
            <SelectItem key={item.value} value={String(item.value)}>
              {item.label} ({item.count.toLocaleString('vi-VN')})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={pestGroup} onValueChange={onPestGroupChange}>
        <SelectTrigger className="w-52 max-md:w-full" aria-label="Lọc theo phân nhóm">
          <SelectValue placeholder="Phân nhóm" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_PESTICIDE_OPTIONS}>Tất cả phân nhóm</SelectItem>
          {(options?.pest_groups ?? []).map((item) => (
            <SelectItem key={item.value} value={item.value}>
              {item.value} ({item.count.toLocaleString('vi-VN')})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={sector} onValueChange={onSectorChange}>
        <SelectTrigger className="w-52 max-md:w-full" aria-label="Lọc theo lĩnh vực">
          <SelectValue placeholder="Lĩnh vực" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_PESTICIDE_OPTIONS}>Tất cả lĩnh vực</SelectItem>
          {(options?.sectors ?? []).map((item) => (
            <SelectItem key={item.value} value={item.value}>
              {toSentenceCaseIfShouting(item.value)} ({item.count.toLocaleString('vi-VN')})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={banned} onValueChange={onBannedChange}>
        <SelectTrigger className="w-56 max-md:w-full" aria-label="Lọc theo hoạt chất cấm">
          <SelectValue placeholder="Hoạt chất cấm" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL_PESTICIDE_OPTIONS}>Mọi thuốc</SelectItem>
          <SelectItem value={BANNED_ONLY}>
            {/* Đang tải thì chưa biết có danh sách cấm hay không — đừng vội nói «chưa có». */}
            {options ? formatBannedFilterLabel(options.banned_rules, options.banned_count) : 'Có hoạt chất cấm'}
          </SelectItem>
        </SelectContent>
      </Select>
    </>
  )
}
