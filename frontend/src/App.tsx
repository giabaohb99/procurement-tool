import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import Login from './pages/Login'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import AppLayout from './layouts/AppLayout'
import Dashboard from './pages/Dashboard'
import CrudList from './components/CrudList'
import CrudDetail from './components/CrudDetail'
import PurchaseRequestDetail from './pages/PurchaseRequestDetail'
import PrintPurchaseRequest from './pages/PrintPurchaseRequest'
import SurveyDetail from './pages/SurveyDetail'
import PurchaseOrderDetail from './pages/PurchaseOrderDetail'
import PrintPurchaseOrder from './pages/PrintPurchaseOrder'
import PrintPurchaseOrderMH from './pages/PrintPurchaseOrderMH'
import Inventory from './pages/Inventory'
import Payables from './pages/Payables'
import PaymentRequestDetail from './pages/PaymentRequestDetail'
import Reports from './pages/Reports'
import SupplierDetail from './pages/SupplierDetail'
import ContractDetail from './pages/ContractDetail'
import RolePermissions from './pages/RolePermissions'
import UserPermissionDetail from './pages/UserPermissionDetail'
import PrintPaymentRequest from './pages/PrintPaymentRequest'

function Protected({ children }: { children: JSX.Element }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/print/purchase-request/:id" element={<Protected><PrintPurchaseRequest /></Protected>} />
          <Route path="/print/purchase-order/:id" element={<Protected><PrintPurchaseOrder /></Protected>} />
          <Route path="/print/purchase-order-mh/:id" element={<Protected><PrintPurchaseOrderMH /></Protected>} />
          <Route path="/print/payment-request/:id" element={<Protected><PrintPaymentRequest /></Protected>} />
          <Route path="/" element={<Protected><AppLayout /></Protected>}>
            <Route index element={<Dashboard />} />
            <Route path="purchase-requests/:id" element={<PurchaseRequestDetail />} />
            <Route path="surveys-supplier/:id" element={<SurveyDetail type="supplier" />} />
            <Route path="surveys-product/:id" element={<SurveyDetail type="product" />} />
            <Route path="purchase-orders/:id" element={<PurchaseOrderDetail />} />
            <Route path="payment-requests/:id" element={<PaymentRequestDetail />} />
            <Route path="inventory" element={<Inventory />} />
            <Route path="payables" element={<Payables />} />
            <Route path="reports" element={<Reports />} />
            <Route path="suppliers/:id" element={<SupplierDetail />} />
            <Route path="contracts/:id" element={<ContractDetail />} />
            <Route path="roles" element={<RolePermissions />} />
            <Route path="users/:id" element={<UserPermissionDetail />} />
            <Route path=":entity" element={<CrudList />} />
            <Route path=":entity/:id" element={<CrudDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
