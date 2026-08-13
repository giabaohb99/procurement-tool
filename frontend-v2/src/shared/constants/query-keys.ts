/**
 * Query key tập trung một chỗ. Trải rác chuỗi thô trong component là nguyên nhân
 * số 1 của lỗi "sửa xong mà danh sách không tự nạp lại" — invalidate trượt key.
 *
 * Quy ước: `[<module>, <entity>, <tham số>]` để invalidate được theo tầng
 * (`queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })`).
 */
export const queryKeys = {
  procurement: {
    all: ['procurement'] as const,
    purchaseRequests: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-requests', params ?? {}] as const,
    purchaseRequest: (id: number) => ['procurement', 'purchase-requests', id] as const,
    /** Số đã đặt theo mã hàng của một phiếu YCMH. */
    purchaseRequestProgress: (id: number) =>
      ['procurement', 'purchase-requests', id, 'order-progress'] as const,
    surveyRequests: (params?: Record<string, unknown>) =>
      ['procurement', 'survey-requests', params ?? {}] as const,
    purchaseOrders: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-orders', params ?? {}] as const,
    purchaseOrder: (id: number) => ['procurement', 'purchase-orders', id] as const,
    surveys: (params?: Record<string, unknown>) =>
      ['procurement', 'surveys', params ?? {}] as const,
    purchaseProgress: (params?: Record<string, unknown>) =>
      ['procurement', 'purchase-progress', params ?? {}] as const,
    surveyReport: (params?: Record<string, unknown>) =>
      ['procurement', 'survey-report', params ?? {}] as const,
    /** Số liệu trang Tổng quan Thu mua (`/api/dashboard/overview`). */
    dashboard: () => ['procurement', 'dashboard'] as const,
  },
  production: {
    all: ['production'] as const,
    // Danh mục NCC nằm ở phân hệ Sản xuất (không phải Thu mua).
    suppliers: (params?: Record<string, unknown>) =>
      ['production', 'suppliers', params ?? {}] as const,
    supplier: (id: number) => ['production', 'suppliers', id] as const,
  },
  hr: {
    all: ['hr'] as const,
    employees: (params?: Record<string, unknown>) =>
      ['hr', 'employees', params ?? {}] as const,
    employee: (id: number) => ['hr', 'employees', id] as const,
    departments: (params?: Record<string, unknown>) =>
      ['hr', 'departments', params ?? {}] as const,
    department: (id: number) => ['hr', 'departments', id] as const,
    companies: (params?: Record<string, unknown>) =>
      ['hr', 'companies', params ?? {}] as const,
    company: (id: number) => ['hr', 'companies', id] as const,
    roles: (params?: Record<string, unknown>) => ['hr', 'roles', params ?? {}] as const,
    /** Danh sách entity/action/scope để dựng ma trận — gần như bất biến. */
    permissionMeta: () => ['hr', 'permission-meta'] as const,
    rolePermissions: (roleId: number) => ['hr', 'roles', roleId, 'permissions'] as const,
    userAccounts: (params?: Record<string, unknown>) =>
      ['hr', 'users', params ?? {}] as const,
    userAccount: (id: number) => ['hr', 'users', id] as const,
    userScope: (userId: number, roleId: number) =>
      ['hr', 'users', userId, 'scope', roleId] as const,
  },
  // Phân hệ đang tắt — giữ chỗ để bật lại không phải nghĩ lại quy ước key.
  sales: {
    all: ['sales'] as const,
  },
  inventory: {
    all: ['inventory'] as const,
  },
  finance: {
    all: ['finance'] as const,
  },
} as const
