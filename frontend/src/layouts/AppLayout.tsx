import { useState, useEffect } from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { toast } from "../components/toast";
import { api } from "../api/client";
import NotificationBell from "../components/NotificationBell";
import PwaInstallPrompt from "../components/PwaInstallPrompt";
import { canInstall, onInstallChange, promptInstall } from "../pwa-install";

type NavItem = {
  to: string;
  label: string;
  icon: string;
  entity?: string;
  manage?: boolean;
  anyEntity?: string[];   // hiện nếu có read trên BẤT KỲ entity nào (OR)
};
type NavGroup = {
  title?: string;
  key?: string;
  collapsible?: boolean;
  items: NavItem[];
};

const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { to: "/", label: "Trang chủ", icon: "ti-layout-dashboard" },
      {
        to: "/reports",
        label: "Báo cáo mua hàng",
        icon: "ti-chart-bar",
        entity: "report",
      },
    ],
  },
  {
    title: "Mua hàng",
    items: [
      {
        to: "/survey-requests",
        label: "Yêu cầu báo giá",
        icon: "ti-clipboard-list",
        entity: "survey_request",
      },
      {
        to: "/purchase-requests",
        label: "Yêu cầu mua hàng",
        icon: "ti-file-text",
        entity: "purchase_request",
      },
      {
        to: "/purchase-orders",
        label: "Đơn mua hàng",
        icon: "ti-shopping-cart",
        entity: "purchase_order",
      },
      {
        to: "/purchase-progress",
        label: "Tiến độ mua hàng",
        icon: "ti-truck-delivery",
        anyEntity: ["purchase_order", "purchase_request"],
      },
    ],
  },
  {
    title: "Khảo sát",
    items: [
      {
        to: "/surveys",
        label: "Phiếu khảo sát",
        icon: "ti-clipboard-search",
        entity: "survey",
      },
      {
        to: "/survey-report",
        label: "Báo cáo khảo sát",
        icon: "ti-report-analytics",
        entity: "survey",
      },
    ],
  },
  {
    title: "Kho & Công nợ",
    items: [
      {
        to: "/inventory",
        label: "Tồn kho",
        icon: "ti-packages",
        entity: "inventory",
      },
      { to: "/payables", label: "Công nợ", icon: "ti-cash", entity: "payable" },
      {
        to: "/payment-requests",
        label: "Yêu cầu thanh toán",
        icon: "ti-receipt",
        entity: "payment_request",
      },
    ],
  },
  {
    title: "Danh mục",
    key: "danhmuc",
    collapsible: true,
    items: [
      {
        to: "/suppliers",
        label: "Nhà cung cấp",
        icon: "ti-truck",
        entity: "supplier",
        manage: true,
      },
      {
        to: "/products",
        label: "Sản phẩm",
        icon: "ti-box",
        entity: "product",
        manage: true,
      },
      {
        to: "/contracts",
        label: "Hợp đồng",
        icon: "ti-file-certificate",
        entity: "contract",
        manage: true,
      },
      {
        to: "/warehouses",
        label: "Kho",
        icon: "ti-building-warehouse",
        entity: "warehouse",
        manage: true,
      },
      {
        to: "/units",
        label: "Đơn vị tính",
        icon: "ti-ruler-2",
        entity: "unit",
        manage: true,
      },
      {
        to: "/item-groups",
        label: "Phân loại",
        icon: "ti-category",
        entity: "item_group",
        manage: true,
      },
      {
        to: "/departments",
        label: "Phòng ban",
        icon: "ti-tag",
        entity: "department",
        manage: true,
      },
      {
        to: "/category-assignees",
        label: "Phân công phụ trách",
        icon: "ti-user-cog",
        entity: "category_assignee",
        manage: true,
      },
    ],
  },
  {
    title: "Hệ thống",
    items: [
      {
        to: "/companies",
        label: "Công ty",
        icon: "ti-building",
        entity: "company",
        manage: true,
      },
      {
        to: "/employees",
        label: "Nhân sự",
        icon: "ti-users",
        entity: "employee",
        manage: true,
      },
      {
        to: "/roles",
        label: "Vai trò",
        icon: "ti-shield",
        entity: "role",
        manage: true,
      },
      {
        to: "/settings",
        label: "Cấu hình hệ thống",
        icon: "ti-settings",
        entity: "setting",
      },
      {
        to: "/import-batches",
        label: "Quản lý Import",
        icon: "ti-file-import",
        entity: "import",
      },
    ],
  },
];
const ALL_ITEMS = NAV_GROUPS.flatMap((g) => g.items);

const isActive = (path: string, to: string) =>
  to === "/" ? path === "/" : path.startsWith(to);

export default function AppLayout() {
  const { user, login, logout, updateUser, can } = useAuth();
  const isDev = import.meta.env.VITE_DEVELOPER_MODE === "dev";
  const devAccounts = [
    "admin",
    "TESTREQ",
    "DEMOAD",
    "DEMOQL",
    "DEMONV",
    "DEMOTP",
  ];

  async function handleDevLogin(username: string) {
    if (!username) return;
    try {
      await login(username, username);
      toast.success(`Đã chuyển sang tài khoản ${username}`);
      window.location.href = "/"; // Tải lại toàn bộ ứng dụng
    } catch (e: any) {
      toast.error(
        "Lỗi chuyển tài khoản: " + (e.response?.data?.message || e.message),
      );
    }
  }

  // Menu "quản lý" (danh mục, hệ thống) chỉ hiện khi được QUẢN LÝ (write/create/delete),
  // không hiện chỉ vì có read (read dùng để đổ dropdown trong form).
  const canManage = (e: string) =>
    can(e, "write") || can(e, "create") || can(e, "delete");
  const visibleItems = (items: NavItem[]) =>
    items.filter(
      (n) =>
        (n.anyEntity ? n.anyEntity.some((e) => can(e, "read")) : true) &&
        (!n.entity || (n.manage ? canManage(n.entity) : can(n.entity, "read"))),
    );
  const nav = useNavigate();
  const loc = useLocation();
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  // Nút "Cài ứng dụng" trong menu — hiện khi trình duyệt cho cài (Edge/Chrome/Android)
  const [installable, setInstallable] = useState(canInstall());
  useEffect(() => onInstallChange(() => setInstallable(canInstall())), []);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem("nav_collapsed") || "{}");
    } catch {
      return {};
    }
  });
  const toggle = (k: string) =>
    setCollapsed((s) => {
      const n = { ...s, [k]: !s[k] };
      localStorage.setItem("nav_collapsed", JSON.stringify(n));
      return n;
    });
  const current = [...ALL_ITEMS]
    .reverse()
    .find((n) => isActive(loc.pathname, n.to));
  const currentGroup = NAV_GROUPS.find((g) =>
    g.items.some((n) => n.to === current?.to),
  );
  const name = user?.full_name || "Người dùng";
  const initials =
    name.trim().split(" ").slice(-1)[0]?.[0]?.toUpperCase() || "U";

  async function handleAvatarUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingAvatar(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post("/api/auth/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      updateUser({ avatar: res.data.data.avatar });
    } catch (err) {
      toast.error("Không thể tải ảnh lên. Vui lòng thử lại.");
    } finally {
      setUploadingAvatar(false);
    }
  }

  return (
    <div className="app">
      {open && <div className="backdrop" onClick={() => setOpen(false)} />}
      <aside className={"sidebar" + (open ? " open" : "")}>
        <div className="brand">
          <div className="brand-logo">
            <img src="/logo.svg" alt="DEGO Holding" />
          </div>
        </div>
        {NAV_GROUPS.map((g, gi) => {
          const items = visibleItems(g.items);
          if (items.length === 0) return null;
          const isCol = g.collapsible && g.key && collapsed[g.key];
          return (
            <div key={gi}>
              {g.title &&
                (g.collapsible ? (
                  <button
                    className="nav-group-title toggle"
                    onClick={() => toggle(g.key!)}
                  >
                    <i
                      className={
                        "ti " + (isCol ? "ti-chevron-right" : "ti-chevron-down")
                      }
                      style={{ fontSize: 13 }}
                    />
                    {g.title}
                  </button>
                ) : (
                  <div className="nav-group-title">{g.title}</div>
                ))}
              {!isCol &&
                items.map((n) => (
                  <Link
                    key={n.to}
                    to={n.to}
                    onClick={() => setOpen(false)}
                    className={
                      "nav-item" +
                      (isActive(loc.pathname, n.to) ? " active" : "")
                    }
                  >
                    <i className={"ti " + n.icon} />
                    {n.label}
                  </Link>
                ))}
            </div>
          );
        })}
      </aside>
      <div className="main">
        <div className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              className="icon-btn hamburger"
              onClick={() => setOpen(true)}
              aria-label="Menu"
            >
              <i className="ti ti-menu-2" />
            </button>
            <div className="crumb">
              {currentGroup?.title ? `${currentGroup.title} / ` : ""}
              {current?.label || "Trang chủ"}
            </div>
          </div>
          <div
            className="topbar-right"
            style={{
              position: "relative",
              display: "flex",
              alignItems: "center",
              gap: 16,
            }}
          >
            {isDev && (
              <select
                style={{
                  padding: "4px 8px",
                  borderRadius: 4,
                  border: "1px solid #ccc",
                  fontSize: 13,
                  background: "#fff",
                  cursor: "pointer",
                  outline: "none",
                }}
                value=""
                onChange={(e) => handleDevLogin(e.target.value)}
              >
                <option value="" disabled>
                  — Đổi user (Dev) —
                </option>
                {devAccounts.map((acc) => (
                  <option key={acc} value={acc}>
                    {acc}
                  </option>
                ))}
              </select>
            )}
            <NotificationBell />
            <div
              style={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                gap: 8,
              }}
              onClick={() => setProfileOpen(!profileOpen)}
            >
              {user?.avatar ? (
                <img
                  src={user.avatar}
                  alt="avatar"
                  className="avatar"
                  style={{ objectFit: "cover" }}
                />
              ) : (
                <span className="avatar">{initials}</span>
              )}
              <span
                className="user-name"
                style={{ fontSize: 13, whiteSpace: "nowrap" }}
              >
                {name}
              </span>
              <i
                className="ti ti-chevron-down"
                style={{ fontSize: 12, color: "#666", flexShrink: 0 }}
              />
            </div>

            {profileOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  right: 0,
                  marginTop: 8,
                  backgroundColor: "white",
                  borderRadius: 8,
                  boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                  width: 250,
                  zIndex: 100,
                  overflow: "hidden",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div
                  style={{
                    padding: 16,
                    borderBottom: "1px solid #eee",
                    backgroundColor: "#f8fafc",
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <label
                    style={{
                      cursor: "pointer",
                      position: "relative",
                      display: "block",
                      flexShrink: 0,
                    }}
                  >
                    {user?.avatar ? (
                      <img
                        src={user.avatar}
                        alt="avatar"
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: "50%",
                          objectFit: "cover",
                          border: "2px solid #fff",
                          boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: "50%",
                          backgroundColor: "#0f172a",
                          color: "#fff",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 20,
                          fontWeight: 600,
                        }}
                      >
                        {initials}
                      </div>
                    )}
                    <div
                      style={{
                        position: "absolute",
                        bottom: 0,
                        right: 0,
                        backgroundColor: "#1c9cf0",
                        color: "#fff",
                        width: 20,
                        height: 20,
                        borderRadius: "50%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
                      }}
                    >
                      <i
                        className={
                          uploadingAvatar ? "ti ti-loader" : "ti ti-camera"
                        }
                        style={{
                          fontSize: 12,
                          animation: uploadingAvatar
                            ? "spin 1s linear infinite"
                            : "none",
                        }}
                      />
                    </div>
                    <input
                      type="file"
                      hidden
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      disabled={uploadingAvatar}
                    />
                  </label>
                  <div>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: 14,
                        color: "#1e293b",
                      }}
                    >
                      {user?.full_name}
                    </div>
                    <div
                      style={{
                        fontSize: 13,
                        color: "#64748b",
                        marginTop: 4,
                        wordBreak: "break-all",
                      }}
                    >
                      {user?.email}
                    </div>
                  </div>
                </div>
                <div style={{ padding: "8px 0" }}>
                  <div
                    style={{
                      padding: "8px 16px",
                      fontSize: 13,
                      color: "#475569",
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <i className="ti ti-phone" style={{ fontSize: 15 }} />{" "}
                    {user?.phone || "Chưa cập nhật SĐT"}
                  </div>
                  <div
                    style={{
                      padding: "8px 16px",
                      fontSize: 13,
                      color: "#475569",
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <i className="ti ti-building" style={{ fontSize: 15 }} />{" "}
                    {user?.department_name || "Chưa có phòng ban"}
                  </div>
                </div>
                <div style={{ borderTop: "1px solid #eee", padding: 8 }}>
                  {installable && (
                    <button
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "8px 8px",
                        backgroundColor: "transparent",
                        border: "none",
                        color: "var(--teal)",
                        cursor: "pointer",
                        borderRadius: 4,
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        fontSize: 13,
                        fontWeight: 500,
                      }}
                      onClick={async () => { setProfileOpen(false); await promptInstall(); setInstallable(canInstall()); }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f1f5f9")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <i className="ti ti-download" style={{ fontSize: 16 }} /> Cài ứng dụng
                    </button>
                  )}
                  <button
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "8px 8px",
                      backgroundColor: "transparent",
                      border: "none",
                      color: "var(--navy)",
                      cursor: "pointer",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 13,
                      fontWeight: 500,
                    }}
                    onClick={() => { setProfileOpen(false); nav("/me"); }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f1f5f9")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                  >
                    <i className="ti ti-user" style={{ fontSize: 16 }} /> Trang cá nhân
                  </button>
                  <button
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "8px 8px",
                      backgroundColor: "transparent",
                      border: "none",
                      color: "#ef4444",
                      cursor: "pointer",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 13,
                      fontWeight: 500,
                    }}
                    onClick={() => {
                      logout();
                      nav("/login");
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.backgroundColor = "#fef2f2")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.backgroundColor = "transparent")
                    }
                  >
                    <i className="ti ti-logout" style={{ fontSize: 16 }} /> Đăng
                    xuất
                  </button>
                </div>
              </div>
            )}

            {profileOpen && (
              <div
                style={{ position: "fixed", inset: 0, zIndex: 99 }}
                onClick={() => setProfileOpen(false)}
              />
            )}
          </div>
        </div>
        <div className="content">
          <Outlet />
        </div>
      </div>
      {import.meta.env.VITE_PWA_INSTALL_PROMPT === 'on' && <PwaInstallPrompt />}
    </div>
  );
}
