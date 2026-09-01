import { Select } from 'antd'
import { useTranslation } from 'react-i18next'

export default function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const handleChange = (value: string) => {
    i18n.changeLanguage(value)
    localStorage.setItem('language', value)
  }

  return (
    <Select
      value={i18n.language}
      onChange={handleChange}
      className="w-28"
      size="small"
      options={[
        { value: 'zh', label: '中文' },
        { value: 'en', label: 'English' },
      ]}
    />
  )
}
