import { useState } from 'react'
import { Card, Upload, Select, Modal, Descriptions, Tag, Alert, Typography, Space, Button, message } from 'antd'
import { InboxOutlined, CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import { useImportWechatBill, useImportAlipayBill, useAccounts } from '../../api/hooks'
import type { ImportResult } from '../../types'

const { Text } = Typography
const { Dragger } = Upload

export default function BillImport() {
  const { t } = useTranslation()
  const importWechat = useImportWechatBill()
  const importAlipay = useImportAlipayBill()
  const { data: accounts } = useAccounts()

  const [wechatAccountId, setWechatAccountId] = useState<number | undefined>()
  const [alipayAccountId, setAlipayAccountId] = useState<number | undefined>()
  const [resultModal, setResultModal] = useState<{ format: string; result: ImportResult } | null>(null)

  function handleImport(platform: 'wechat' | 'alipay', file: File) {
    const mut = platform === 'wechat' ? importWechat : importAlipay
    const accountId = platform === 'wechat' ? wechatAccountId : alipayAccountId

    mut.mutateAsync({ file, accountId }).then((resp) => {
      const data = resp.data
      setResultModal({
        format: platform,
        result: data,
      })
      if (data.errors.length === 0) {
        message.success(t('importExport.importSuccess', { created: data.created, skipped: data.skipped }))
      } else {
        message.warning(t('importExport.importWithErrors', { count: data.errors.length }))
      }
    }).catch(() => {})

    return false // prevent upload
  }

  return (
    <div>
      <PageHeader title={t('billImport.title')} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 微信账单导入 */}
        <Card title={t('billImport.wechatTitle')}>
          <Space direction="vertical" className="w-full" size="middle">
            <Text type="secondary">{t('billImport.wechatDesc')}</Text>

            <div>
              <Text className="mb-1 block">{t('billImport.defaultAccount')}</Text>
              <Select
                allowClear
                placeholder={t('billImport.selectAccount')}
                className="w-full"
                value={wechatAccountId}
                onChange={setWechatAccountId}
                options={accounts?.map(a => ({ value: a.id, label: a.name }))}
              />
            </div>

            <Dragger
              accept=".csv"
              multiple={false}
              showUploadList={false}
              beforeUpload={(file) => handleImport('wechat', file as unknown as File)}
              disabled={importWechat.isPending}
            >
              <p className="ant-upload-drag-icon">
                {importWechat.isPending ? <span>...</span> : <InboxOutlined />}
              </p>
              <p className="ant-upload-text">{t('billImport.clickOrDrag')}</p>
              <p className="ant-upload-hint">{t('billImport.wechatHint')}</p>
            </Dragger>
          </Space>
        </Card>

        {/* 支付宝账单导入 */}
        <Card title={t('billImport.alipayTitle')}>
          <Space direction="vertical" className="w-full" size="middle">
            <Text type="secondary">{t('billImport.alipayDesc')}</Text>

            <div>
              <Text className="mb-1 block">{t('billImport.defaultAccount')}</Text>
              <Select
                allowClear
                placeholder={t('billImport.selectAccount')}
                className="w-full"
                value={alipayAccountId}
                onChange={setAlipayAccountId}
                options={accounts?.map(a => ({ value: a.id, label: a.name }))}
              />
            </div>

            <Dragger
              accept=".csv"
              multiple={false}
              showUploadList={false}
              beforeUpload={(file) => handleImport('alipay', file as unknown as File)}
              disabled={importAlipay.isPending}
            >
              <p className="ant-upload-drag-icon">
                {importAlipay.isPending ? <span>...</span> : <InboxOutlined />}
              </p>
              <p className="ant-upload-text">{t('billImport.clickOrDrag')}</p>
              <p className="ant-upload-hint">{t('billImport.alipayHint')}</p>
            </Dragger>
          </Space>
        </Card>
      </div>

      {/* 导入结果 Modal */}
      <Modal
        title={t('billImport.importResult')}
        open={resultModal !== null}
        onCancel={() => setResultModal(null)}
        footer={<Button type="primary" onClick={() => setResultModal(null)}>{t('common.ok')}</Button>}
      >
        {resultModal && (
          <div className="space-y-4">
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label={t('billImport.platform')}>
                <Tag color={resultModal.format === 'wechat' ? 'green' : 'blue'}>
                  {resultModal.format === 'wechat' ? t('billImport.platformWechat') : t('billImport.platformAlipay')}
                </Tag>
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
                    <Alert key={i} message={err} type="error" showIcon className="text-sm" />
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
