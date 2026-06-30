import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import Login from './pages/Login'
import AppLayout from './layouts/AppLayout'
import Dashboard from './pages/Dashboard'
import CrudList from './components/CrudList'
import CrudDetail from './components/CrudDetail'
import PurchaseRequestDetail from './pages/PurchaseRequestDetail'
import PrintPurchaseRequest from './pages/PrintPurchaseRequest'
import SurveyDetail from './pages/SurveyDetail'

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
          <Route path="/print/purchase-request/:id" element={<Protected><PrintPurchaseRequest /></Protected>} />
          <Route path="/" element={<Protected><AppLayout /></Protected>}>
            <Route index element={<Dashboard />} />
            <Route path="purchase-requests/:id" element={<PurchaseRequestDetail />} />
            <Route path="surveys-supplier/:id" element={<SurveyDetail type="supplier" />} />
            <Route path="surveys-product/:id" element={<SurveyDetail type="product" />} />
            <Route path=":entity" element={<CrudList />} />
            <Route path=":entity/:id" element={<CrudDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
