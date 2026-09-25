import { Filter, X } from 'lucide-react'

import { ConditionalFilter, useFilterQuery } from '@/shared/conditional-filter'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Label } from '@/shared/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { recentBookYears } from '../helpers/recent-book-years'
import { STATUS_LABELS } from '../types/document-record'
import type { DocumentType } from '../types/document-type'

const ALL = 'all'

interface FolderDocumentsFilterToolbarProps {
  keyword: string
  onKeywordChange: (value: string) => void
  documentTypes: DocumentType[]
  typeId: string
  onTypeIdChange: (value: string) => void
  status: string
  onStatusChange: (value: string) => void
  year: string
  onYearChange: (value: string) => void
  includeSubfolders: boolean
  onIncludeSubfoldersChange: (value: boolean) => void
}

/** Chip nhỏ có nút gỡ — cùng khuôn `Badge` + `X` của `folder-chip-list.tsx`, tách một bản riêng vì đây là chip LỌC (không phải chip thư mục). */
function RemovableFilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <Badge variant="secondary" className="gap-1 py-1 pr-1 pl-2 font-normal">
      <span>{label}</span>
      <button
        type="button"
        aria-label={`Bỏ lọc "${label}"`}
        onClick={onRemove}
        className="flex size-4 shrink-0 items-center justify-center rounded-full hover:bg-black/10"
      >
        <X className="size-3" />
      </button>
    </Badge>
  )
}

/**
 * HÀNG 2 GỌN kiểu Drive (đặc tả A + đợt dọn gọn, phản hồi 24/09/2026 tối) — ô
 * tìm + ĐÚNG MỘT nút «Bộ lọc» (huy hiệu đếm số điều kiện đang bật) mở popover
 * chứa Loại/Trạng thái/Năm/«Gồm thư mục con»/«Bộ lọc nâng cao» (công tắc «Tìm cả nội dung» bỏ 25/09/2026 — gõ đủ 2 ký tự là tự tìm cả nội dung) — không còn dãy
 * Select/Switch LUÔN HIỆN trên thanh công cụ (khách chê "show ra hết thì
 * xấu"). Điều kiện đang bật hiện thành CHIP gỡ được ngay dưới ô tìm, CHỈ khi
 * có gì đang lọc — hàng chip biến mất hoàn toàn lúc mọi thứ về mặc định.
 *
 * ⚠️ KHÔNG còn ô sắp xếp/nút đổi chiều ở đây — sắp xếp nay bấm THẲNG vào tiêu
 * đề cột (chế độ Danh sách, `folder-list-view.tsx`) hoặc nhãn nhỏ phía trên
 * lưới (chế độ Lưới, `folder-documents-view.tsx`), giống Google Drive.
 */
export function FolderDocumentsFilterToolbar({
  keyword,
  onKeywordChange,
  documentTypes,
  typeId,
  onTypeIdChange,
  status,
  onStatusChange,
  year,
  onYearChange,
  includeSubfolders,
  onIncludeSubfoldersChange,
}: FolderDocumentsFilterToolbarProps) {
  //  Đếm CẢ điều kiện nâng cao (`ConditionalFilter`, chạy trong `FilterProvider`
  //  của `folder-documents-table.tsx`) lẫn ba ô lọc nhanh + công tắc thư mục con, cho
  //  huy hiệu trên nút «Bộ lọc» phản ánh ĐỦ mọi thứ đang lọc chứ không riêng
  //  một tầng. «Gồm thư mục con» đếm khi BẬT (mặc định TẮT từ 24/09/2026).
  const { activeCount: advancedCount } = useFilterQuery()
  const quickCount =
    (typeId !== ALL ? 1 : 0) +
    (status !== ALL ? 1 : 0) +
    (year !== ALL ? 1 : 0) +
    (includeSubfolders ? 1 : 0)
  const totalCount = advancedCount + quickCount
  const typeLabel = documentTypes.find((type) => String(type.id) === typeId)?.name
  const statusLabel = STATUS_LABELS[Number(status)]

  return (
    <div className="flex flex-1 flex-col gap-1.5">
      <div className="flex flex-1 flex-wrap items-center gap-2">
        <SearchField
          value={keyword}
          onChange={onKeywordChange}
          placeholder="Tìm tên, số hiệu, từ khóa…"
          placeholderShort="Tìm tên, số hiệu…"
          className="min-w-56 max-w-sm flex-1"
        />

        <Popover>
          <PopoverTrigger asChild>
            <Button type="button" variant="outline" size="sm" className="shrink-0 gap-1.5">
              <Filter className="size-4" />
              Bộ lọc
              {totalCount > 0 && (
                <Badge variant="default" className="h-4 rounded-full px-1.5 text-[10px]">
                  {totalCount}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent align="start" className="w-72 space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="folder-filter-type">Loại văn bản</Label>
              <Select value={typeId} onValueChange={onTypeIdChange}>
                <SelectTrigger id="folder-filter-type" className="w-full" aria-label="Lọc theo loại văn bản">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại</SelectItem>
                  {documentTypes.map((type) => (
                    <SelectItem key={type.id} value={String(type.id)}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="folder-filter-status">Trạng thái</Label>
              <Select value={status} onValueChange={onStatusChange}>
                <SelectTrigger id="folder-filter-status" className="w-full" aria-label="Lọc theo trạng thái">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {Object.entries(STATUS_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="folder-filter-year">Năm hiệu lực</Label>
              <Select value={year} onValueChange={onYearChange}>
                <SelectTrigger id="folder-filter-year" className="w-full" aria-label="Lọc theo năm hiệu lực">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi năm</SelectItem>
                  {recentBookYears().map((option) => (
                    <SelectItem key={option} value={String(option)}>
                      Năm {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="folder-filter-subfolders" className="font-normal">
                Gồm thư mục con
              </Label>
              <Switch
                id="folder-filter-subfolders"
                checked={includeSubfolders}
                onCheckedChange={onIncludeSubfoldersChange}
              />
            </div>

            <div className="border-t pt-2">
              <ConditionalFilter variant="ghost" className="w-full justify-start px-0" />
            </div>
          </PopoverContent>
        </Popover>
      </div>

      {quickCount > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {typeId !== ALL && typeLabel && (
            <RemovableFilterChip label={typeLabel} onRemove={() => onTypeIdChange(ALL)} />
          )}
          {status !== ALL && statusLabel && (
            <RemovableFilterChip label={statusLabel} onRemove={() => onStatusChange(ALL)} />
          )}
          {year !== ALL && <RemovableFilterChip label={`Năm ${year}`} onRemove={() => onYearChange(ALL)} />}
          {includeSubfolders && (
            <RemovableFilterChip
              label="Gồm thư mục con"
              onRemove={() => onIncludeSubfoldersChange(false)}
            />
          )}
        </div>
      )}
    </div>
  )
}
