import { lazy, Suspense, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider, Spin, theme as antTheme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { useTranslation } from 'react-i18next'
import { useAppStore } from './stores/appStore'
import { useConnectionStore } from './stores/connectionStore'
import AppLayout from './components/layout/AppLayout'
import ErrorBoundary from './components/common/ErrorBoundary'
import ServiceUnavailable from './pages/ServiceUnavailable'
import client from './api/client'

const Dashboard = lazy(() => import('./pages/Dashboard'))
// 统一资产管理
const AssetManagement = lazy(() => import('./pages/AssetManagement'))
const AssetForm = lazy(() => import('./pages/AssetForm'))
// 分类
const SubscriptionPeriods = lazy(() => import('./pages/SubscriptionPeriods'))
const Categories = lazy(() => import('./pages/Categories'))
// 其他
const ImportExport = lazy(() => import('./pages/ImportExport'))
const AuditLog = lazy(() => import('./pages/AuditLog'))
const Login = lazy(() => import('./pages/Login'))
const TransactionList = lazy(() => import('./pages/Transactions/index'))
const TransactionForm = lazy(() => import('./pages/Transactions/TransactionForm'))
const Accounts = lazy(() => import('./pages/Accounts/index'))
const TransactionCategories = lazy(() => import('./pages/TransactionCategories/index'))
const BillImport = lazy(() => import('./pages/BillImport/index'))
const AssetTypes = lazy(() => import('./pages/AssetTypes'))

function App() {
  const [authChecked, setAuthChecked] = useState(false)
  const { theme: appTheme } = useAppStore()
  const { i18n } = useTranslation()
  const antdLocale = i18n.language === 'en' ? enUS : zhCN
  const isDark = appTheme === 'dark'
  const connectionStatus = useConnectionStore((s) => s.status)
  const checkConnection = useConnectionStore((s) => s.checkConnection)

  useEffect(() => {
    // First check health/connection
    checkConnection()
  }, [checkConnection])

  useEffect(() => {
    // Only proceed to auth check after connection is established
    if (connectionStatus === 'connected') {
      // Probe auth status so the 401 interceptor can redirect if needed
      client.get('/auth/status').finally(() => setAuthChecked(true))
    }
  }, [connectionStatus])

  // Show loading while checking connection
  if (connectionStatus === 'checking') return <Spin fullscreen />

  // Show ServiceUnavailable if connection failed
  if (connectionStatus === 'disconnected') return <ServiceUnavailable />

  // Connection OK, but still checking auth
  if (!authChecked) return <Spin fullscreen />

  return (
    <ErrorBoundary>
      <ConfigProvider
        locale={antdLocale}
        theme={{
          algorithm: isDark ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
        }}
      >
        <div className={isDark ? 'dark' : ''}>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={
                <Suspense fallback={<Spin />}><ErrorBoundary><Login /></ErrorBoundary></Suspense>
              } />
              <Route element={<AppLayout />}>
                <Route path="/" element={<Suspense fallback={<Spin />}><ErrorBoundary><Dashboard /></ErrorBoundary></Suspense>} />
                {/* 统一资产管理 */}
                <Route path="/asset-management" element={<Suspense fallback={<Spin />}><ErrorBoundary><AssetManagement /></ErrorBoundary></Suspense>} />
                <Route path="/assets/new" element={<Suspense fallback={<Spin />}><ErrorBoundary><AssetForm /></ErrorBoundary></Suspense>} />
                <Route path="/assets/:id/edit" element={<Suspense fallback={<Spin />}><ErrorBoundary><AssetForm /></ErrorBoundary></Suspense>} />
                {/* 记账 */}
                <Route path="/transactions" element={<Suspense fallback={<Spin />}><ErrorBoundary><TransactionList /></ErrorBoundary></Suspense>} />
                <Route path="/transactions/new" element={<Suspense fallback={<Spin />}><ErrorBoundary><TransactionForm /></ErrorBoundary></Suspense>} />
                <Route path="/transactions/:id/edit" element={<Suspense fallback={<Spin />}><ErrorBoundary><TransactionForm /></ErrorBoundary></Suspense>} />
                {/* 账户 */}
                <Route path="/accounts" element={<Suspense fallback={<Spin />}><ErrorBoundary><Accounts /></ErrorBoundary></Suspense>} />
                {/* 记账分类 */}
                <Route path="/transaction-categories" element={<Suspense fallback={<Spin />}><ErrorBoundary><TransactionCategories /></ErrorBoundary></Suspense>} />
                <Route path="/bill-import" element={<Suspense fallback={<Spin />}><ErrorBoundary><BillImport /></ErrorBoundary></Suspense>} />
                {/* 分类管理 */}
                <Route path="/categories" element={<Suspense fallback={<Spin />}><ErrorBoundary><Categories /></ErrorBoundary></Suspense>} />
                <Route path="/subscription-periods" element={<Suspense fallback={<Spin />}><ErrorBoundary><SubscriptionPeriods /></ErrorBoundary></Suspense>} />
                {/* 资产类型 */}
                <Route path="/asset-types" element={<Suspense fallback={<Spin />}><ErrorBoundary><AssetTypes /></ErrorBoundary></Suspense>} />
                {/* 其他 */}
                <Route path="/import-export" element={<Suspense fallback={<Spin />}><ErrorBoundary><ImportExport /></ErrorBoundary></Suspense>} />
                <Route path="/audit-log" element={<Suspense fallback={<Spin />}><ErrorBoundary><AuditLog /></ErrorBoundary></Suspense>} />
              </Route>
            </Routes>
          </BrowserRouter>
        </div>
      </ConfigProvider>
    </ErrorBoundary>
  )
}

export default App
