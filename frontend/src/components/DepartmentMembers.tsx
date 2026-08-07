import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

// Danh sách nhân sự thuộc phòng ban (hiện dưới form ở trang chi tiết phòng ban).
// Trưởng bộ phận (managerId) được đưa lên đầu + gắn huy hiệu "Trưởng BP".
export default function DepartmentMembers({ departmentId, managerId }: { departmentId: number; managerId?: number }) {
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (!departmentId) return
    setLoading(true)
    api.get('/api/employees', { params: { department_id: departmentId, page_size: 200 }, _silent: true } as any)
      .then((r) => {
        const items: any[] = r.data.data.items || []
        // Trưởng BP lên đầu, còn lại theo tên
        items.sort((a, b) => {
          if (a.id === managerId) return -1
          if (b.id === managerId) return 1
          return String(a.full_name || '').localeCompare(String(b.full_name || ''))
        })
        setRows(items)
      })
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
  }, [departmentId, managerId])

  return (
    <div className="card" style={{ padding: 18 }}>
      {/* Cùng kiểu tiêu đề section với thẻ "Lịch sử thao tác" ở CrudDetail */}
      <h3 className="sec-title" style={{ marginTop: 0 }}>
        <i className="ti ti-users" style={{ marginRight: 8, color: '#b6c2d9' }} />
        Nhân sự thuộc phòng ({rows.length})
      </h3>
      {loading ? (
        <div style={{ color: '#999', fontSize: 13 }}>Đang tải…</div>
      ) : rows.length === 0 ? (
        <div style={{ color: '#999', fontSize: 13 }}>Chưa có nhân sự</div>
      ) : (
        <table>
          <thead>
            <tr><th>Mã NV</th><th>Họ tên</th><th>Chức danh</th></tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.id} className="clickable" onClick={() => navigate(`/employees/${e.id}`)}>
                <td>{e.code}</td>
                <td>
                  {e.full_name}
                  {e.id === managerId && (
                    <span className="badge ok" style={{ marginLeft: 8 }}>Trưởng BP</span>
                  )}
                </td>
                <td>{e.position || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
