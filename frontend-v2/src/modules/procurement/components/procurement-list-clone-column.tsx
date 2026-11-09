import type { DataTableColumn } from '@/shared/data-table'
import { ProcurementListCloneRowButton } from './procurement-list-clone-controls'

interface CloneColumnOptions<T> {
  apiPath: string
  getId: (row: T) => number
  getCode: (row: T) => string | undefined
  toDetail: (id: number) => string
  successMessage: string
  errorMessage: string
}

/**
 * Cột *Thao tác* của chế độ nhân bản (duoc-CR-741, theo `CrudList.tsx` bản v1): chỉ
 * dựng khi người dùng bật nút *Nhân bản* ở đầu trang. Hàm thuần trả khai báo cột nên
 * gọi được ngay trong `useMemo` của màn danh sách — cùng kiểu `createSelectionColumn`.
 */
export function createCloneColumn<T>({
  apiPath,
  getId,
  getCode,
  toDetail,
  successMessage,
  errorMessage,
}: CloneColumnOptions<T>): DataTableColumn<T> {
  return {
    key: 'clone',
    header: 'Thao tác',
    width: 120,
    minWidth: 100,
    align: 'center',
    hideable: false,
    //  Ghim mép phải như cột cố định của v1: bảng rộng hơn khung, để cột nằm cuối thì
    //  bật chế độ xong không thấy gì thay đổi nếu chưa cuộn ngang.
    stickyRight: true,
    cell: (row) => (
      <ProcurementListCloneRowButton
        apiPath={apiPath}
        id={getId(row)}
        code={getCode(row)}
        toDetail={toDetail}
        successMessage={successMessage}
        errorMessage={errorMessage}
      />
    ),
  }
}
