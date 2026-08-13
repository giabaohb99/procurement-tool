/**
 * Đường dẫn tập trung — sửa URL một chỗ, không phải grep chuỗi khắp nơi.
 * Mỗi module đóng góp một nhánh; `routes.tsx` của module dùng chính hằng số này.
 */
export const appRoutes = {
  login: '/login',
  forgotPassword: '/forgot-password',
  /** Màn chọn phân hệ — trang chủ sau khi đăng nhập. */
  launcher: '/',

  sales: {
    root: '/sales',
  },
  inventory: {
    root: '/inventory',
  },
  procurement: {
    root: '/procurement',
    /** Yêu cầu báo giá (YCBG) — bước đầu của luồng mua hàng. */
    surveyRequests: '/procurement/survey-requests',
    /** Yêu cầu mua hàng (PYC). */
    purchaseRequests: '/procurement/purchase-requests',
    purchaseRequestNew: '/procurement/purchase-requests/new',
    purchaseRequestDetail: (id: number | string) =>
      `/procurement/purchase-requests/${id}`,
    purchaseRequestPrint: (id: number | string) => `/print/purchase-request/${id}`,
    /** Đơn mua hàng (ĐMH). */
    purchaseOrders: '/procurement/purchase-orders',
    purchaseOrderNew: '/procurement/purchase-orders/new',
    purchaseOrderDetail: (id: number | string) => `/procurement/purchase-orders/${id}`,
    purchaseOrderPrint: (id: number | string) => `/print/purchase-order/${id}`,
    /** Báo cáo tiến độ theo từng lần giao hàng. */
    purchaseProgress: '/procurement/purchase-progress',
    /** Phiếu khảo sát NCC / sản phẩm. */
    surveys: '/procurement/surveys',
    /** Báo cáo khảo sát, cắt theo dòng khảo sát. */
    surveyReport: '/procurement/survey-report',
  },
  finance: {
    root: '/finance',
  },
  customer: {
    root: '/customer',
  },
  project: {
    root: '/project',
  },
  document: {
    root: '/document',
    /** Văn bản đến / đi / nội bộ. */
    documents: '/document/documents',
    documentNew: '/document/documents/new',
    documentDetail: (id: number | string) => `/document/documents/${id}`,
    /** Sổ văn bản đến / đi / nội bộ theo số vào sổ. */
    books: '/document/books',
    /**
     * Thiết lập văn bản — bốn danh mục nền (loại, mức mật/khẩn, đối tác, trường
     * thông tin) nằm chung một trang, phân biệt bằng `?tab=`.
     */
    settings: '/document/settings',
    settingsTab: (tab: 'types' | 'security-levels' | 'partners' | 'fields') =>
      `/document/settings?tab=${tab}`,
    /** Loại văn bản (công văn, quyết định…). */
    typeNew: '/document/types/new',
    typeDetail: (id: number | string) => `/document/types/${id}`,
    /** Mức mật / khẩn. */
    securityLevelNew: '/document/security-levels/new',
    securityLevelDetail: (id: number | string) => `/document/security-levels/${id}`,
    /** Đối tác văn bản. */
    partnerNew: '/document/partners/new',
    partnerDetail: (id: number | string) => `/document/partners/${id}`,
    /** Trường thông tin động. */
    fieldNew: '/document/fields/new',
    fieldDetail: (id: number | string) => `/document/fields/${id}`,
  },
  report: {
    root: '/report',
  },
  system: {
    root: '/system',
  },
  production: {
    root: '/production',
    /** Danh mục nhà cung cấp / đơn vị vận chuyển — thuộc phân hệ Sản xuất. */
    suppliers: '/production/suppliers',
    supplierDetail: (id: number | string) => `/production/suppliers/${id}`,
  },
  hr: {
    root: '/hr',
    employees: '/hr/employees',
    employeeDetail: (id: number | string) => `/hr/employees/${id}`,
    departments: '/hr/departments',
    departmentDetail: (id: number | string) => `/hr/departments/${id}`,
    companies: '/hr/companies',
    companyDetail: (id: number | string) => `/hr/companies/${id}`,
    /** Ma trận vai trò × quyền + danh sách tài khoản. */
    permissions: '/hr/permissions',
    /** Gán vai trò và phạm vi dữ liệu cho MỘT tài khoản. */
    userPermissionDetail: (userId: number | string) => `/hr/permissions/users/${userId}`,
  },
} as const
