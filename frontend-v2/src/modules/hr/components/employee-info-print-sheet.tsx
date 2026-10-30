import { CONTACT_COLUMNS } from '../config/employee-contact-columns'
import { FAMILY_COLUMNS } from '../config/employee-family-columns'
import {
  EMPLOYEE_INFO_FORM_CODE,
  EMPLOYEE_INFO_FORM_ISSUED,
  EMPLOYEE_INFO_PRINT_SECTIONS,
  PRINT_MIN_PEOPLE_ROWS,
  PRINT_WIDE_FIELDS,
  type PrintFieldSection,
} from '../config/employee-info-print-sections'
import {
  EMPLOYEE_FIELD_DEFS,
  formatEmployeeFieldValue,
  type EmployeeFieldKey,
} from '../config/employee-profile-fields'
import type { PeopleColumn } from './employee-people-editor'
import type { Employee, EmployeeContact, EmployeeFamily } from '../types/employee'
import { formatPeopleCell } from '../utils/format-people-cell'
import { cn } from '@/shared/utils/cn'

interface EmployeeInfoPrintSheetProps {
  employee: Employee
  contacts: readonly EmployeeContact[]
  families: readonly EmployeeFamily[]
}

/**
 * Giá trị in của một ô hồ sơ.
 *
 * Ô mã số ưu tiên NHÃN backend gửi kèm (`<ô>_label`) — bộ mã số của hồ sơ gõ tay ở TS dễ lệch
 * backend (xem `profile-hr-details.tsx`); không có nhãn thì mới tra bảng mã bên này.
 * Ô bị backend che (thiếu `employee_sensitive.read`) về `''` / `null` → in ô TRỐNG.
 */
function readPrintValue(employee: Employee, field: EmployeeFieldKey): string {
  const source = employee as unknown as Record<string, unknown>
  if (EMPLOYEE_FIELD_DEFS[field].kind === 'code') {
    const label = source[`${field}_label`]
    if (typeof label === 'string' && label) return label
  }
  return formatEmployeeFieldValue(field, source[field])
}

function FieldSection({ section, employee }: { section: PrintFieldSection; employee: Employee }) {
  return (
    <section className="mt-4 break-inside-avoid">
      <h2 className="mb-1.5 font-bold" style={{ fontSize: '11.5pt' }}>
        {section.title}
      </h2>
      <div className="grid grid-cols-2 gap-x-6">
        {section.fields.map((field) => (
          <div
            key={field}
            className={cn('flex items-end gap-2 py-[3px]', PRINT_WIDE_FIELDS.has(field) && 'col-span-2')}
          >
            <span className="shrink-0">{EMPLOYEE_FIELD_DEFS[field].label}:</span>
            {/*  Gạch chân CHẤM thay cho ô viền: cùng lối điền tay của phiếu giấy, ô trống vẫn thấy
                 chỗ để viết vào. */}
            <span className="min-h-[1.3em] min-w-0 flex-1 border-b border-dotted border-black font-semibold [overflow-wrap:anywhere]">
              {readPrintValue(employee, field)}
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}

function PeopleTable<T>({
  title,
  note,
  columns,
  rows,
}: {
  title: string
  note?: string
  columns: PeopleColumn<T>[]
  rows: readonly T[]
}) {
  //  Luôn chừa tối thiểu vài dòng trống: phiếu này còn được in ra để người mới vào điền tay.
  const blanks = Math.max(PRINT_MIN_PEOPLE_ROWS - rows.length, 0)
  return (
    <section className="mt-4 break-inside-avoid">
      <h2 className="font-bold" style={{ fontSize: '11.5pt' }}>
        {title}
      </h2>
      {note && <p className="mb-1.5 text-[10pt] italic">{note}</p>}
      <table className="w-full table-fixed border-collapse text-[10pt]">
        <thead>
          <tr>
            <th className="w-8 border border-black px-1 py-1 text-center">STT</th>
            {columns.map((col) => (
              <th key={col.key} className="border border-black px-1.5 py-1 text-left">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              <td className="border border-black px-1 py-1 text-center">{index + 1}</td>
              {columns.map((col) => (
                <td key={col.key} className="border border-black px-1.5 py-1 align-top">
                  {formatPeopleCell(col.kind, row[col.key])}
                </td>
              ))}
            </tr>
          ))}
          {Array.from({ length: blanks }, (_, i) => (
            <tr key={`trong-${i}`}>
              <td className="h-7 border border-black px-1 py-1 text-center">{rows.length + i + 1}</td>
              {columns.map((col) => (
                <td key={col.key} className="border border-black px-1.5 py-1" />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

/**
 * Mặt phiếu "PHIẾU THÔNG TIN NHÂN VIÊN" khổ A4 (duoc-CR-676, C5). Chỉ dựng giấy từ dữ liệu đã
 * nạp — không gọi API, nên trang in cho phòng Nhân sự và trang in "của tôi" dùng chung.
 *
 * Thứ tự mục / ô nằm ở `EMPLOYEE_INFO_PRINT_SECTIONS` (tệp mẫu BM00 gốc chưa có, xem ghi chú ở đó).
 */
export function EmployeeInfoPrintSheet({ employee, contacts, families }: EmployeeInfoPrintSheetProps) {
  return (
    <div
      className="a4-print-sheet mx-auto bg-white text-black shadow-xl"
      style={{
        width: '210mm',
        minHeight: '297mm',
        padding: '15mm 18mm',
        fontFamily: "'Times New Roman', Times, serif",
        fontSize: '11pt',
        lineHeight: 1.4,
        boxSizing: 'border-box',
      }}
    >
      <header className="flex items-start justify-between gap-4">
        <div className="max-w-[60%] font-bold uppercase">{employee.company_name || ''}</div>
        <div className="shrink-0 text-right text-[10pt]">
          <div>Mã số: {EMPLOYEE_INFO_FORM_CODE}</div>
          <div>{EMPLOYEE_INFO_FORM_ISSUED}</div>
        </div>
      </header>

      <h1 className="mt-6 mb-2 text-center font-bold" style={{ fontSize: '16pt' }}>
        PHIẾU THÔNG TIN NHÂN VIÊN
      </h1>

      {EMPLOYEE_INFO_PRINT_SECTIONS.map((section) => {
        if (section.kind === 'fields') {
          return <FieldSection key={section.title} section={section} employee={employee} />
        }
        if (section.kind === 'contacts') {
          return (
            <PeopleTable<EmployeeContact>
              key={section.title}
              title={section.title}
              note={section.note}
              columns={CONTACT_COLUMNS}
              rows={contacts}
            />
          )
        }
        return (
          <PeopleTable<EmployeeFamily>
            key={section.title}
            title={section.title}
            note={section.note}
            columns={FAMILY_COLUMNS}
            rows={families}
          />
        )
      })}

      <p className="mt-5 text-[10pt] italic">
        Tôi cam đoan những thông tin khai trên là đúng sự thật và chịu trách nhiệm về nội dung đã khai.
      </p>

      <div className="mt-4 flex justify-between break-inside-avoid text-center">
        {['Người khai', 'Phòng Nhân sự'].map((title) => (
          <div key={title} className="flex w-[44%] flex-col items-center">
            <div className="italic">Ngày ...... tháng ...... năm 20......</div>
            <div className="mt-1 font-bold">{title}</div>
            <div className="text-[10pt] italic">(Ký và ghi rõ họ tên)</div>
            <div className="h-20" />
            <div className="font-bold">{title === 'Người khai' ? employee.full_name : ''}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
