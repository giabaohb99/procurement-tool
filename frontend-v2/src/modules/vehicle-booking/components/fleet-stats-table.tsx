import { Inbox } from 'lucide-react'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import { compactMoney } from '../utils/compact-money'

interface VehicleStatRow {
  id: number
  label: string
  total: number
  completed: number
  distance_km: number
  cost: number
}

interface DriverStatRow {
  id: number
  name: string
  total: number
  completed: number
  distance_km: number
}

/** Số km gọn: 1.250 -> "1.250"; 0 -> "—". */
function km(value: number): string {
  return value > 0 ? value.toLocaleString('vi-VN') : '—'
}

function EmptyRow({ span }: { span: number }) {
  return (
    <TableRow>
      <TableCell colSpan={span}>
        <div className="flex flex-col items-center gap-1 py-6 text-muted-foreground">
          <Inbox className="size-6" />
          <span className="text-sm">Chưa có dữ liệu trong khoảng đã chọn.</span>
        </div>
      </TableCell>
    </TableRow>
  )
}

/**
 * Bảng "Thống kê theo xe" — số phiếu · hoàn tất · (km) · (chi phí).
 *
 * ⚠️ Hai cột **Km** và **Chi phí** chỉ dựng khi CÓ ÍT NHẤT MỘT dòng có số. Hai
 * cột đó đầy đủ chỉ khi văn thư nhập km và chi phí lúc đóng chuyến, mà phần lớn
 * chuyến nội thành không ai nhập — bày ra thì được một cột dấu gạch chạy dọc cả
 * bảng, chiếm chỗ ngang với cột có số thật. Còn một dòng có số thì cột vẫn hiện,
 * vì lúc đó dấu gạch mới mang nghĩa "chuyến này chưa nhập".
 */
export function VehicleStatsTable({ rows }: { rows: VehicleStatRow[] }) {
  const showKm = rows.some((r) => r.distance_km > 0)
  const showCost = rows.some((r) => r.cost > 0)
  const span = 3 + (showKm ? 1 : 0) + (showCost ? 1 : 0)

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Xe</TableHead>
          <TableHead className="text-right">Số phiếu</TableHead>
          <TableHead className="text-right">Hoàn tất</TableHead>
          {showKm && <TableHead className="text-right">Km</TableHead>}
          {showCost && <TableHead className="text-right">Chi phí</TableHead>}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.length === 0 ? (
          <EmptyRow span={span} />
        ) : (
          rows.map((r) => (
            <TableRow key={r.id}>
              <TableCell className="font-medium">{r.label}</TableCell>
              <TableCell className="text-right tabular-nums">{r.total}</TableCell>
              <TableCell className="text-right tabular-nums text-muted-foreground">{r.completed}</TableCell>
              {showKm && (
                <TableCell className="text-right tabular-nums text-muted-foreground">
                  {km(r.distance_km)}
                </TableCell>
              )}
              {showCost && (
                <TableCell className="text-right tabular-nums">
                  {r.cost > 0 ? `${compactMoney(r.cost)} đ` : '—'}
                </TableCell>
              )}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
}

/** Bảng "Thống kê theo tài xế" — số phiếu · hoàn tất · (km). Cột Km ẩn khi cả bảng rỗng. */
export function DriverStatsTable({ rows }: { rows: DriverStatRow[] }) {
  const showKm = rows.some((r) => r.distance_km > 0)

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Tài xế</TableHead>
          <TableHead className="text-right">Số phiếu</TableHead>
          <TableHead className="text-right">Hoàn tất</TableHead>
          {showKm && <TableHead className="text-right">Km</TableHead>}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.length === 0 ? (
          <EmptyRow span={showKm ? 4 : 3} />
        ) : (
          rows.map((r) => (
            <TableRow key={r.id}>
              <TableCell className="font-medium">{r.name}</TableCell>
              <TableCell className="text-right tabular-nums">{r.total}</TableCell>
              <TableCell className="text-right tabular-nums text-muted-foreground">{r.completed}</TableCell>
              {showKm && (
                <TableCell className="text-right tabular-nums text-muted-foreground">
                  {km(r.distance_km)}
                </TableCell>
              )}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
}
