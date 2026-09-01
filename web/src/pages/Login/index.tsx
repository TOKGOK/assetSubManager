import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import client from '../../api/client'

export default function Login() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { password: string }) => {
    setLoading(true)
    try {
      const { data } = await client.post('/auth/login', { password: values.password })
      if (data.data?.token) {
        localStorage.setItem('auth_token', data.data.token)
      }
      message.success(t('auth.loginSuccess'))
      window.location.href = '/'
    } catch {
      // interceptor handles error display
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <Card className="w-96">
        <h2 className="text-xl font-bold text-center mb-6">{t('app.title')}</h2>
        <Form onFinish={onFinish}>
          <Form.Item name="password" rules={[{ required: true, message: t('auth.passwordRequired') }]}>
            <Input.Password prefix={<LockOutlined />} placeholder={t('auth.password')} size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              {t('auth.login')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
