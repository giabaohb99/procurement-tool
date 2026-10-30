import { Download, FileCheck2 } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'

import { LaborContractStatusBadge } from '@/modules/hr/components/labor-contract-status-badge'
import { formatContractPeriod } from '@/modules/hr/config/employee-labor-contract-columns'
import { myLaborContractApi } from '@/modules/hr/api/my-labor-contract-api'
import { useMyLaborContracts } from '@/modules/hr/hooks/use-my-labor-contracts'
import type { MyLaborContract } from '@/modules/hr/types/my-labor-contract'
import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { formatMoney } from '@/shared/utils/format-money'

/** Tên gợi ý khi server không gửi tên tệp. */
const fallbackName = (row: MyLaborContract, ext: string) => `HDLD-${row.contract_no || row.code}.${ext}`

/**
 * MỤC "Hợp đồng của tôi" của Trang cá nhân (duoc-CR-652) — CHỈ ĐỌC.
 *
 * Backend chỉ trả HĐ của chính người đăng nhập ở trạng thái Đã ký / Đã chấm dứt / Hết hạn (Nháp, Đã hủy không hiện),
 * nên giao diện không cần và không có nút sửa / sinh tệp / tải bản ký lên / chuyển trạng thái / xóa. Hai nút tải
 * hiện theo cờ `has_*_file`; lương hiện vì là hợp đồng của chính mình.
 *
 * Chỉ dựng khi tài khoản đã gắn hồ sơ nhân sự — gác ở `profile-page.tsx` / `profile-sections.ts`.
 */
export function ProfileLaborContractsTab() {
  const { data, isLoading, isError } = useMyLaborContracts()
  const [busyIds, setBusyIds] = useState<ReadonlySet<number>>(new Set())

  /** Khóa nút của dòng trong lúc tải. Lỗi đã được toast sẵn bởi http-client. */
  const run = useCallback(async (id: number, task: () => Promise<unknown>) => {
    setBusyIds((prev) => new Set(prev).add(id))
    try {
      await task()
    } catch {
      //  http-client đã toast câu lỗi tiếng Việt của backend.
    } finally {
      setBusyIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }, [])

  const columns = useMemo<DataTableColumn<MyLaborContract>[]>(
    () => [
      {
        key: 'contract_no',
        header: 'Số HĐ',
        width: 150,
        hideable: false,
        wrap: true,
        cell: (r) => (
          <span>
            {r.contract_no || r.code}
            {r.contract_no && <span className="block text-xs text-muted-foreground">{r.code}</span>}
          </span>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        cell: (r) => <LaborContractStatusBadge status={r.effective_status} />,
      },
      {
        key: 'contract_type',
        header: 'Loại',
        width: 140,
        wrap: true,
        cell: (r) => labelOf(LABOR_CONTRACT_TYPE, String(r.contract_type)) || '—',
      },
      {
        key: 'period',
        header: 'Hiệu lực',
        width: 190,
        cell: (r) => formatContractPeriod(r.start_date, r.end_date),
      },
      { key: 'job_title', header: 'Chức danh', width: 140, wrap: true, cell: (r) => r.job_title || '—' },
      {
        key: 'base_salary',
        header: 'Lương cơ bản',
        width: 130,
        align: 'right',
        cell: (r) => formatMoney(r.base_salary),
      },
      {
        key: 'actions',
        header: 'Tệp',
        width: 280,
        hideable: false,
        cell: (r) => (
          <div className="flex flex-wrap gap-2">
            {r.has_generated_file && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busyIds.has(r.id)}
                onClick={() =>
                  void run(r.id, () => myLaborContractApi.downloadDocument(r.id, fallbackName(r, 'docx')))
                }
              >
                <Download className="size-4" />
                Tải bản mềm (.docx)
              </Button>
            )}
            {r.has_signed_file && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busyIds.has(r.id)}
                onClick={() =>
                  void run(r.id, () => myLaborContractApi.downloadSignedFile(r.id, fallbackName(r, 'pdf')))
                }
              >
                <FileCheck2 className="size-4" />
                Xem / tải bản đã ký
              </Button>
            )}
            {!r.has_generated_file && !r.has_signed_file && (
              <span className="text-xs text-muted-foreground">Chưa có tệp</span>
            )}
          </div>
        ),
      },
    ],
    [busyIds, run],
  )

  return (
    <DataTable
      columns={columns}
      rows={data?.items}
      getRowId={(r) => r.id}
      isLoading={isLoading}
      isError={isError}
      errorMessage="Không tải được danh sách hợp đồng."
      emptyMessage="Bạn chưa có hợp đồng lao động nào đã ký."
      storageKey="me.labor-contracts"
      filtersActive={false}
    />
  )
}
