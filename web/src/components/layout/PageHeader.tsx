import { Space, Typography } from 'antd'

const { Title } = Typography

interface PageHeaderProps {
  title: string
  extra?: React.ReactNode
}

export default function PageHeader({ title, extra }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-4">
      <Title level={4} className="!mb-0">{title}</Title>
      <Space>{extra}</Space>
    </div>
  )
}
