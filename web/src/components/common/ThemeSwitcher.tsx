import { Button, Tooltip } from 'antd'
import { SunOutlined, MoonOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '../../stores/appStore'

export default function ThemeSwitcher() {
  const { t } = useTranslation()
  const { theme, toggleTheme } = useAppStore()
  const isDark = theme === 'dark'

  return (
    <Tooltip title={isDark ? t('common.switchToLight') : t('common.switchToDark')}>
      <Button
        type="text"
        icon={isDark ? <SunOutlined /> : <MoonOutlined />}
        onClick={toggleTheme}
      />
    </Tooltip>
  )
}
