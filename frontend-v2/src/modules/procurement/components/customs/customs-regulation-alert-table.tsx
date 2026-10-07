// Bảng cảnh báo pháp lý theo từ khóa đang tra — dòng NẶNG NHẤT lên đầu (bao-CR-477): tra
// «Ethylene glycol» ra bốn danh sách thì thứ cần thấy trước là dòng có nghĩa vụ.
import { useMemo } from 'react'

import { DataTable } from '@/shared/data-table'

import { CUSTOMS_REGULATION_COLUMNS } from '../../config/customs-regulation-columns'
import type { CustomsRegulationHit } from '../../types/customs'
import { sortRegulationsBySeverity } from '../../utils/customs'

interface CustomsRegulationAlertTableProps {
  items: CustomsRegulationHit[]
}

export function CustomsRegulationAlertTable({ items }: CustomsRegulationAlertTableProps) {
  const sortedItems = useMemo(() => sortRegulationsBySeverity(items), [items])
  return (
    <DataTable
      columns={CUSTOMS_REGULATION_COLUMNS}
      rows={sortedItems}
      getRowId={(row) => row.id}
      //  07/10/2026 — STT của phụ lục đứng ĐẦU bảng (đại ca chốt); cột ID tự thêm (bao-CR-578) là số
      //  nội bộ của DB, không có trong văn bản, và luôn chen lên trước mọi cột → tắt riêng ở bảng này.
      idColumn={false}
      emptyMessage="Không có mục nào."
    />
  )
}
