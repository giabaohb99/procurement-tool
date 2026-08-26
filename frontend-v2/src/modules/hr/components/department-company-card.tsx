import { Loader2, Plus, Save, Trash2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import { useCompanies } from '../hooks/use-companies'
import { useDepartmentCompanies, useSaveDepartmentCompanies } from '../hooks/use-departments'
import { useEmployees } from '../hooks/use-employees'
import type { DepartmentCompanyInput } from '../types/department'
import { LookupSelect } from './lookup-select'

interface DepartmentCompanyCardProps {
  departmentId: number
  primaryCompanyId: number
  canWrite: boolean
}

/** A06 — một phòng ban có thể dùng chung ở nhiều pháp nhân, mỗi nơi một trưởng phòng. */
export function DepartmentCompanyCard({
  departmentId,
  primaryCompanyId,
  canWrite,
}: DepartmentCompanyCardProps) {
  const { data, isLoading, dataUpdatedAt } = useDepartmentCompanies(departmentId)
  //  Tên trưởng bộ phận đang lưu, tra theo pháp nhân — để ô chọn hiện đúng tên
  //  cả khi người đó bị lọc khỏi danh sách (dữ liệu cũ: trưởng phòng thuộc pháp
  //  nhân khác). Không có nó thì ô hiện `#4`.
  const savingFieldName = new Map(
    (data ?? []).map((row) => [row.company_id, row.manager_name]),
  )
  const initialRows = (data ?? []).map(
    ({ company_id, manager_employee_id, issue_code_override, is_active }) => ({
      company_id,
      manager_employee_id,
      issue_code_override,
      is_active,
    }),
  )

  // Query đổi dữ liệu thì `key` đổi, dựng lại editor với draft mới mà không cần
  // đồng bộ setState trong effect (tránh một lượt render trung gian dữ liệu cũ).
  return (
    <DepartmentCompanyEditor
      key={dataUpdatedAt}
      departmentId={departmentId}
      primaryCompanyId={primaryCompanyId}
      canWrite={canWrite}
      initialRows={initialRows}
      savingFieldName={savingFieldName}
      isLoading={isLoading}
    />
  )
}

interface DepartmentCompanyEditorProps extends DepartmentCompanyCardProps {
  initialRows: DepartmentCompanyInput[]
  /** pháp nhân → tên trưởng bộ phận đang lưu. Xem chỗ dựng nó ở trên. */
  savingFieldName: Map<number, string>
  isLoading: boolean
}

function DepartmentCompanyEditor({
  departmentId,
  primaryCompanyId,
  canWrite,
  initialRows,
  savingFieldName,
  isLoading,
}: DepartmentCompanyEditorProps) {
  const save = useSaveDepartmentCompanies(departmentId)
  // Nạp cả dòng đã ngừng để cấu hình lịch sử vẫn hiển thị đúng tên; chỉ cho
  // thêm/chọn mới pháp nhân và nhân sự đang hoạt động.
  const { data: companies } = useCompanies({ page_size: 1000 })
  const { data: employees } = useEmployees({ page_size: 1000 })
  const [rows, setRows] = useState<DepartmentCompanyInput[]>(initialRows)

  const availableCompanyIds = useMemo(() => {
    const used = new Set(rows.map((row) => row.company_id))
    return (companies?.items ?? [])
      .filter((company) => company.is_active && !used.has(company.id))
      .map((company) => company.id)
  }, [companies?.items, rows])

  function updateRow(index: number, patch: Partial<DepartmentCompanyInput>) {
    setRows((current) =>
      current.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)),
    )
  }

  function addRow() {
    const companyId = availableCompanyIds[0]
    if (!companyId) return
    setRows((current) => [
      ...current,
      {
        company_id: companyId,
        manager_employee_id: null,
        issue_code_override: '',
        is_active: true,
      },
    ])
  }

  function removeRow(index: number) {
    setRows((current) => current.filter((_, rowIndex) => rowIndex !== index))
  }

  async function handleSave() {
    const companyIds = rows.map((row) => row.company_id)
    if (new Set(companyIds).size !== companyIds.length) {
      toast.error('Một pháp nhân chỉ được chọn một lần')
      return
    }
    if (primaryCompanyId && !companyIds.includes(primaryCompanyId)) {
      toast.error('Phải giữ pháp nhân gốc của phòng ban')
      return
    }
    await save.mutateAsync(rows)
  }

  return (
    <Card className="gap-4">
      <CardHeader>
        <CardTitle>Pháp nhân áp dụng</CardTitle>
        <CardDescription>
          Khai phòng ban dùng chung ở pháp nhân nào, trưởng bộ phận tại từng nơi và mã phòng ban
          riêng nếu có.
        </CardDescription>
        {canWrite && (
          <CardAction className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={addRow}
              disabled={!availableCompanyIds.length || save.isPending}
            >
              <Plus />
              Thêm pháp nhân
            </Button>
            <Button type="button" onClick={handleSave} disabled={save.isPending}>
              {save.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              Lưu cấu hình
            </Button>
          </CardAction>
        )}
      </CardHeader>

      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-64">Pháp nhân</TableHead>
              <TableHead className="min-w-64">Trưởng bộ phận tại pháp nhân</TableHead>
              <TableHead className="w-44">Mã phòng ban riêng</TableHead>
              <TableHead className="w-28 text-center">Áp dụng</TableHead>
              {canWrite && <TableHead className="w-14" />}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={canWrite ? 5 : 4} className="py-8 text-center">
                  <Loader2 className="mx-auto animate-spin text-muted-foreground" />
                </TableCell>
              </TableRow>
            ) : rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={canWrite ? 5 : 4}
                  className="py-8 text-center text-muted-foreground"
                >
                  Chưa khai pháp nhân áp dụng.
                </TableCell>
              </TableRow>
            ) : (
              rows.map((row, index) => {
                const isPrimary = row.company_id === primaryCompanyId
                const companyOptions = (companies?.items ?? [])
                  .filter(
                    (company) =>
                      company.id === row.company_id ||
                      (company.is_active && !rows.some((item) => item.company_id === company.id)),
                  )
                  .map((company) => ({
                    id: company.id,
                    label: `${company.issue_code || company.code} — ${company.name}`,
                  }))
                const managerOptions = (employees?.items ?? [])
                  .filter(
                    (employee) =>
                      employee.company_id === row.company_id &&
                      (employee.is_active || employee.id === row.manager_employee_id),
                  )
                  .map((employee) => ({
                    id: employee.id,
                    label: `${employee.code} — ${employee.full_name}`,
                  }))

                return (
                  <TableRow key={`${row.company_id}-${index}`}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="min-w-0 flex-1">
                          <LookupSelect
                            value={row.company_id}
                            onChange={(companyId) =>
                              updateRow(index, {
                                company_id: companyId,
                                manager_employee_id: null,
                              })
                            }
                            items={companyOptions}
                            placeholder="Chọn pháp nhân"
                            disabled={!canWrite || isPrimary}
                          />
                        </div>
                        {isPrimary && <Badge variant="secondary">Gốc</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <LookupSelect
                        value={row.manager_employee_id}
                        onChange={(employeeId) =>
                          updateRow(index, {
                            manager_employee_id: employeeId || null,
                          })
                        }
                        items={managerOptions}
                        placeholder="Chọn trưởng bộ phận"
                        emptyLabel="— Chưa chỉ định —"
                        fallbackLabel={savingFieldName.get(row.company_id)}
                        disabled={!canWrite}
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={row.issue_code_override}
                        onChange={(event) =>
                          updateRow(index, {
                            issue_code_override: event.target.value
                              .toUpperCase()
                              .replace(/[^A-Z0-9]/g, ''),
                          })
                        }
                        placeholder="Mặc định"
                        maxLength={20}
                        disabled={!canWrite}
                      />
                    </TableCell>
                    <TableCell className="text-center">
                      <Checkbox
                        checked={row.is_active}
                        onCheckedChange={(checked) =>
                          updateRow(index, { is_active: checked === true })
                        }
                        aria-label="Pháp nhân đang áp dụng"
                        disabled={!canWrite || isPrimary}
                      />
                    </TableCell>
                    {canWrite && (
                      <TableCell>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => removeRow(index)}
                          disabled={isPrimary}
                          aria-label="Bỏ pháp nhân"
                        >
                          <Trash2 />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
        <p className="mt-3 text-xs text-muted-foreground">
          Mã riêng để trống sẽ dùng mã phòng ban mặc định. Nhân sự chỉ hiện trong đúng pháp nhân
          đang chọn.
        </p>
      </CardContent>
    </Card>
  )
}
