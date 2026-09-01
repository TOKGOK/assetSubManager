import { Result, Button } from 'antd'
import { useTranslation } from 'react-i18next'

export default function PageError({ onRetry }: { onRetry?: () => void }) {
  const { t } = useTranslation()

  const handleRetry = () => {
    if (onRetry) {
      onRetry()
    } else {
      window.location.reload()
    }
  }

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Result
        status="500"
        title={t('error.loadFailed')}
        subTitle={t('error.refreshHint')}
        extra={
          <Button type="primary" onClick={handleRetry}>
            {t('error.refresh')}
          </Button>
        }
      />
    </div>
  )
}
