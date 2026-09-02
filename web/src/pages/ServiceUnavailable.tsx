import React from 'react'
import { Result, Button } from 'antd'
import { useTranslation } from 'react-i18next'
import { useConnectionStore } from '../stores/connectionStore'

const ServiceUnavailable: React.FC = () => {
  const { t } = useTranslation()
  const status = useConnectionStore((s) => s.status)
  const checkConnection = useConnectionStore((s) => s.checkConnection)

  return (
    <Result
      status="error"
      title={t('serviceUnavailable.title')}
      subTitle={t('serviceUnavailable.description')}
      extra={
        <Button
          type="primary"
          loading={status === 'checking'}
          onClick={checkConnection}
        >
          {t('serviceUnavailable.retry')}
        </Button>
      }
    />
  )
}

export default ServiceUnavailable
