import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  ImportOutlined,
  FileTextOutlined,
  AccountBookOutlined,
  WalletOutlined,
  FileExcelOutlined,
  TagsOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '../../stores/appStore'
import LanguageSwitcher from '../common/LanguageSwitcher'
import ThemeSwitcher from '../common/ThemeSwitcher'

const { Sider, Content, Header } = Layout

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { sidebarCollapsed, toggleSidebar } = useAppStore()
  const { t } = useTranslation()

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: t('nav.dashboard') },
    { key: '/asset-management', icon: <AppstoreOutlined />, label: t('nav.assetManagement') },
    {
      key: '/category-management',
      icon: <TagsOutlined />,
      label: t('nav.categoryManagement'),
      children: [
        { key: '/categories', icon: <TagsOutlined />, label: t('nav.categories') },
        { key: '/subscription-periods', icon: <ClockCircleOutlined />, label: t('nav.subscriptionPeriods') },
        { key: '/asset-types', icon: <SettingOutlined />, label: t('nav.assetTypes') },
      ],
    },
    { key: '/transactions', icon: <AccountBookOutlined />, label: t('nav.transactions') },
    { key: '/accounts', icon: <WalletOutlined />, label: t('nav.accounts') },
    { key: '/bill-import', icon: <FileExcelOutlined />, label: t('nav.billImport') },
    { key: '/import-export', icon: <ImportOutlined />, label: t('nav.importExport') },
    { key: '/audit-log', icon: <FileTextOutlined />, label: t('nav.auditLog') },
  ]

  return (
    <Layout className="h-screen">
      <Sider
        collapsible
        collapsed={sidebarCollapsed}
        onCollapse={toggleSidebar}
        theme="light"
        className="border-r border-gray-200 dark:border-gray-700"
      >
        <div className="h-16 flex items-center justify-center font-bold text-lg border-b border-gray-200 dark:border-gray-700">
          {sidebarCollapsed ? '📦' : `📦 ${t('app.title')}`}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => {
            // Don't navigate for parent-only menu keys
            if (key === '/category-management') return
            navigate(key)
          }}
          className="border-r-0"
        />
        {!sidebarCollapsed && (
          <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
            <LanguageSwitcher />
          </div>
        )}
      </Sider>
      <Layout>
        <Header className="bg-white dark:bg-[#141414] px-6 flex items-center justify-between border-b border-gray-200 dark:border-gray-700">
          <span className="text-gray-500 dark:text-gray-400">{t('app.title')}</span>
          <div className="flex items-center gap-1">
            <ThemeSwitcher />
            <LanguageSwitcher />
          </div>
        </Header>
        <Content className="p-6 overflow-auto bg-gray-50 dark:bg-[#141414]">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
