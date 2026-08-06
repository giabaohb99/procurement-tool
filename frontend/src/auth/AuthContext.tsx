import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "../api/client";

type Perms = Record<string, Record<string, boolean | string>>;
type User = {
  id: number;
  full_name: string;
  email: string;
  emp_code?: string;
  employee_id?: number;
  phone?: string;
  department_name?: string;
  role_name?: string;
  position?: string;
  avatar?: string;
  permissions: Perms;
};
type Ctx = {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  loginGoogle: (credential: string) => Promise<void>;
  logout: () => void;
  can: (entity: string, action: string) => boolean;
  updateUser: (u: Partial<User>) => void;
};

const AuthCtx = createContext<Ctx>({} as Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const s = localStorage.getItem("user");
    return s ? JSON.parse(s) : null;
  });

  // CR-028: hồ sơ trong localStorage chỉ được ghi lúc ĐĂNG NHẬP nên cứ đứng yên mãi —
  // đổi tên/phòng ban/gắn lại nhân sự hay sửa phân quyền đều không thấy cho tới khi đăng xuất.
  // Mỗi lần mở app (còn token) hỏi lại /auth/me một phát, lỗi thì im lặng dùng bản cũ.
  useEffect(() => {
    if (!localStorage.getItem("token")) return;
    api.get("/api/auth/me", { _silent: true } as any)
      .then((r) => {
        const fresh = r.data?.data;
        if (!fresh) return;
        localStorage.setItem("user", JSON.stringify(fresh));
        setUser(fresh);
      })
      .catch(() => {});
  }, []);

  async function login(username: string, password: string) {
    const r = await api.post("/api/auth/login", { username, password });

    const { access_token, refresh_token, user: loggedUser } = r.data.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    localStorage.setItem("user", JSON.stringify(loggedUser));
    setUser(loggedUser);
  }

  async function loginGoogle(credential: string) {
    const r = await api.post("/api/auth/google", { credential });
    const { access_token, refresh_token, user: loggedUser } = r.data.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    localStorage.setItem("user", JSON.stringify(loggedUser));
    setUser(loggedUser);
  }

  function logout() {
    // Ghi log đăng xuất (best-effort) trước khi xóa token — không chặn nếu lỗi mạng.
    api.post("/api/auth/logout", null, { _silent: true } as any).catch(() => {});
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setUser(null);
  }

  function can(entity: string, action: string) {
    return !!user?.permissions?.[entity]?.[action];
  }

  function updateUser(u: Partial<User>) {
    if (!user) return;
    const nextUser = { ...user, ...u };
    localStorage.setItem("user", JSON.stringify(nextUser));
    setUser(nextUser);
  }

  return (
    <AuthCtx.Provider
      value={{ user, login, loginGoogle, logout, can, updateUser }}
    >
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
