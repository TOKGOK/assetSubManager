import { useState } from 'react'
import { Button, Card, Space, message, Typography, Upload, Modal, Descriptions, Alert, Tag } from 'antd'
import {
  DownloadOutlined, UploadOutlined, DatabaseOutlined,
  InboxOutlined, CheckCircleOutlined, WarningOutlined, CloseCircleOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import {
  useExportCsv, useExportJson, useExportSql,
  useImportCsv, useImportJson, useImportSql,
} from '../../api/hooks'
import type { ImportResult } from '../../types'

const { Text } = Typography
const { Dragger } = Upload

interface ImportResultData {
  format: string
  result: ImportResult
  message: string
}

export default function ImportExport() {
  const { t } = useTranslation()
  const exportCsv = useExportCsv()
  const exportJson = useExportJson()
  const exportSql = useExportSql()
  const importCsv = useImportCsv()
  const importJson = useImportJson()
  const importSql = useImportSql()

  const [resultModal, setResultModal] = useState<ImportResultData | null>(null)

  async function handleExport(
    mut: { mutateAsync: () => Promise<unknown>; isPending: boolean },
    formatKey: string,
  ) {
    if (mut.isPending) return
    try {
      await mut.mutateAsync()
      message.success(t('importExport.exportSuccess', { format: formatKey }))
    } catch {
      // client interceptor already shows error
    }
  }

  function handleImportFile(file: File, format: 'csv' | 'json' | 'sql') {
    if (format === 'sql') {
      importSql.mutateAsync(file).then((resp) => {
        const data = resp.data
        if (data.success) {
          message.success(t('importExport.sqlRestoreSuccess'))
        } else {
          message.error(`${t('importExport.sqlRestoreFailed')}：${data.errors.join(', ')}`)
        }
      }).catch(() => {
        // client interceptor already shows error
      })
      return false
    }
    const mut = format === 'csv' ? importCsv : importJson
    mut.mutateAsync(file).then((resp) => {
      const result = resp.data
      setResultModal({
        format: format.toUpperCase(),
        result,
        message: resp.message || t('importExport.importComplete'),
      })
      if (result.errors.length === 0) {
        message.success(t('importExport.importSuccess', { created: result.created, skipped: result.skipped }))
      } else {
        message.warning(t('importExport.importWithErrors', { count: result.errors.length }))
      }
    }).catch(() => {
      // client interceptor already shows error
    })
    return false
  }

  return (
    <div>
      <PageHeader title={t('importExport.title')} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title={t('importExport.exportData')}>
          <Space direction="vertical" className="w-full">
            <Text type="secondary">{t('importExport.exportDesc')}</Text>
            <Space wrap>
              <Button
                icon={<DownloadOutlined />}
                loading={exportCsv.isPending}
                onClick={() => handleExport(exportCsv, 'CSV')}
              >
                {t('importExport.exportCsv')}
              </Button>
              <Button
                icon={<DownloadOutlined />}
                loading={exportJson.isPending}
                onClick={() => handleExport(exportJson, 'JSON')}
              >
                {t('importExport.exportJson')}
              </Button>
              <Button
                icon={<DatabaseOutlined />}
                loading={exportSql.isPending}
                onClick={() => handleExport(exportSql, 'SQL')}
              >
                {t('importExport.exportSql')}
              </Button>
            </Space>
          </Space>
        </Card>

        <Card title={t('importExport.importData')}>
          <Space direction="vertical" className="w-full" size="middle">
            <Text type="secondary">{t('importExport.importDesc')}</Text>

            <Dragger
              accept=".csv"
              multiple={false}
              showUploadList={false}
              beforeUpload={(file) => handleImportFile(file as unknown as File, 'csv')}
              disabled={importCsv.isPending}
            >
              <p className="ant-upload-drag-icon">
                {importCsv.isPending ? <UploadOutlined spin /> : <InboxOutlined />}
              </p>
              <p className="ant-upload-text">{t('importExport.clickOrDragCsv')}</p>
              <p className="ant-upload-hint">{t('importExport.csvOnly')}</p>
            </Dragger>

            <Dragger
              accept=".json"
              multiple={false}
              showUploadList={false}
              beforeUpload={(file) => handleImportFile(file as unknown as File, 'json')}
              disabled={importJson.isPending}
            >
              <p className="ant-upload-drag-icon">
                {importJson.isPending ? <UploadOutlined spin /> : <InboxOutlined />}
              </p>
              <p className="ant-upload-text">{t('importExport.clickOrDragJson')}</p>
              <p className="ant-upload-hint">{t('importExport.jsonOnly')}</p>
            </Dragger>

            <Dragger
              accept=".sql"
              multiple={false}
              showUploadList={false}
              beforeUpload={(file) => handleImportFile(file as unknown as File, 'sql')}
              disabled={importSql.isPending}
            >
              <p className="ant-upload-drag-icon">
                {importSql.isPending ? <UploadOutlined spin /> : <InboxOutlined />}
              </p>
              <p className="ant-upload-text">{t('importExport.clickOrDragSql')}</p>
              <p className="ant-upload-hint">{t('importExport.sqlWarning')}</p>
            </Dragger>
          </Space>
        </Card>
      </div>

      <Modal
        title={t('importExport.importResult')}
        open={resultModal !== null}
        onCancel={() => setResultModal(null)}
        footer={
          <Button type="primary" onClick={() => setResultModal(null)}>
            {t('common.ok')}
          </Button>
        }
      >
        {resultModal && (
          <div className="space-y-4">
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label={t('importExport.format')}>
                <Tag color="blue">{resultModal.format}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('importExport.created')}>
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  <Text strong>{resultModal.result.created}</Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label={t('importExport.skipped')}>
                <Space>
                  <WarningOutlined style={{ color: '#faad14' }} />
                  <Text strong>{resultModal.result.skipped}</Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label={t('importExport.errors')}>
                <Space>
                  <CloseCircleOutlined style={{ color: resultModal.result.errors.length > 0 ? '#ff4d4f' : '#52c41a' }} />
                  <Text strong>{resultModal.result.errors.length}</Text>
                </Space>
              </Descriptions.Item>
            </Descriptions>

            {resultModal.result.errors.length > 0 && (
              <div>
                <Text strong className="mb-2 block">{t('importExport.errorDetails')}</Text>
                <div className="max-h-48 overflow-y-auto space-y-1">
                  {resultModal.result.errors.map((err, i) => (
                    <Alert
                      key={i}
                      message={err}
                      type="error"
                      showIcon
                      className="text-sm"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
