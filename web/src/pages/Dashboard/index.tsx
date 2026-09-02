import { useMemo, useEffect, useState } from 'react'
import { Card, Col, Row, Statistic, Table, List, Tag, Typography, theme, Result } from 'antd'
import {
  DollarOutlined, AppstoreOutlined, SyncOutlined, CheckCircleOutlined,
} from '@ant-design/icons'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import client from '../../api/client'
import { useDashboard, useCategoryStats } from '../../api/hooks'

// ---------------------------------------------------------------------------
// Chart palette — first 6 slots of the validated default categorical palette
// (see dataviz/references/palette.md). Worst adjacent CVD ΔE ≥ 8 in both modes.
// Slots 4–6 (yellow, magenta, green) sit below 3:1 contrast on the light
// surface, so the pie carries direct labels (name + percent) as relief.
// ---------------------------------------------------------------------------
const COLORS_LIGHT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
const COLORS_DARK  = ['#3987e5', '#d95926', '#199e7a', '#c98500', '#d55181', '#008300']

// Single-series bar uses the sequential blue ramp — one hue, the title names
// the series, no legend box needed (single series → no legend, per the method).
const BAR_LIGHT = '#2a78d6'
const BAR_DARK  = '#3987e5'

/** Pie label: "name  xx%" rendered outside the slice in text-secondary ink. */
function renderPieLabel({
  cx, x, y, name, percent,
}: {
  cx: number; x: number; y: number;
  name: string; percent: number;
}) {
  return (
    <text
      x={x}
      y={y}
      textAnchor={x >= cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="fill-[var(--chart-text)] text-xs"
    >
      {`${name}  ${(percent * 100).toFixed(0)}%`}
    </text>
  )
}

/**
 * Track whether the page is in dark mode by watching for the `.dark` class on
 * `<html>`. This matches the Tailwind `darkMode: 'class'` strategy used by the
 * app. We use a MutationObserver (not a one-shot check) so the chart palette
 * follows the theme toggle in real time.
 */
function useIsDark(): boolean {
  const [isDark, setIsDark] = useState(() => {
    if (typeof document === 'undefined') return false
    return document.documentElement.classList.contains('dark')
  })
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'))
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])
  return isDark
}

export default function Dashboard() {
  const { t } = useTranslation()
  const { token } = theme.useToken()
  const isDark = useIsDark()

  const { data: dashboard, isLoading, isError } = useDashboard()
  const { data: categoryStats } = useCategoryStats()
  const { data: reminders, isError: remindersError } = useQuery({
    queryKey: ['subscription-reminders'],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: any[] }>('/subscriptions/reminders?days=30')
      return data.data
    },
    staleTime: 60_000,
  })

  // Theme-adaptive palette: categorical for the pie, sequential blue for the bar.
  const COLORS = isDark ? COLORS_DARK : COLORS_LIGHT
  const BAR_COLOR = isDark ? BAR_DARK : BAR_LIGHT

  // Map backend category keys to localized labels for chart display.
  const TYPE_NAME_KEYS: Record<string, string> = {
    physical: 'dashboard.typeNames.physical',
    virtual: 'dashboard.typeNames.virtual',
    subscription: 'dashboard.typeNames.subscription',
  }

  const pieData = useMemo(() =>
    (categoryStats ?? []).map(item => ({
      ...item,
      name: t(TYPE_NAME_KEYS[item.name as keyof typeof TYPE_NAME_KEYS] ?? item.name),
    })),
    [categoryStats, t]
  )
  const barData = useMemo(() =>
    (categoryStats ?? []).map(item => ({
      ...item,
      name: t(TYPE_NAME_KEYS[item.name as keyof typeof TYPE_NAME_KEYS] ?? item.name),
    })),
    [categoryStats, t]
  )

  // Theme tokens surfaced as CSS custom properties so the SVG chrome (grid,
  // axis text, pie label text) tracks light/dark without per-element JS logic.
  const cssVars = {
    '--chart-grid': token.colorBorderSecondary,
    '--chart-text': token.colorTextSecondary,
    '--chart-axis': token.colorBorder,
  } as React.CSSProperties

  const upcomingCols = [
    { title: t('dashboard.name'), dataIndex: 'name', key: 'name' },
    {
      title: t('dashboard.value'), dataIndex: ['custom_data', 'value'], key: 'value',
      render: (v: number) => `¥${v.toFixed(2)}`,
    },
    { title: t('dashboard.cycle'), dataIndex: 'period_name', key: 'period_name' },
    { title: t('dashboard.dueDate'), dataIndex: 'next_renewal', key: 'next_renewal' },
  ]

  if (isError) return <Result status="warning" title={t('dashboard.loadFailed')} />
  if (isLoading || !dashboard) return <div>{t('common.loading')}</div>

  return (
    <div style={cssVars}>
      {/* ---- Stat tiles ---- */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.totalValue')}
              value={dashboard.total_value}
              prefix={<DollarOutlined />}
              suffix={t('dashboard.unit.yuan')}
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.totalAssets')}
              value={dashboard.total_count}
              prefix={<AppstoreOutlined />}
              suffix={t('dashboard.unit.pieces')}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.monthlySubscription')}
              value={dashboard.monthly_subscription}
              prefix={<SyncOutlined />}
              suffix={t('dashboard.unit.perMonth')}
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.expiringSoon')}
              value={dashboard.upcoming_subscriptions?.length || 0}
              prefix={<CheckCircleOutlined />}
              suffix={t('dashboard.unit.items')}
            />
          </Card>
        </Col>
      </Row>

      {/* ---- Charts row: pie (identity) + bar (magnitude) ---- */}
      <Row gutter={16} className="mt-4">
        <Col xs={24} lg={12}>
          <Card title={t('dashboard.categoryDistribution')}>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label={renderPieLabel}
                    labelLine={{ stroke: token.colorTextQuaternary, strokeWidth: 1 }}
                  >
                    {pieData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={COLORS[i % COLORS.length]}
                        stroke="none"
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: token.colorBgContainer,
                      borderColor: token.colorBorderSecondary,
                      borderRadius: 6,
                    }}
                    formatter={(value: number, name: string) => [`${value} 件`, name]}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: 12, color: token.colorTextSecondary }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-400 dark:text-gray-500 py-10">
                {t('dashboard.noCategoryData')}
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={t('dashboard.categoryValue')}>
            {barData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barData}>
                  {/* Solid hairline grid — never dashed (per the method). */}
                  <CartesianGrid
                    stroke="var(--chart-grid)"
                    strokeDasharray=""
                    strokeWidth={1}
                  />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: 'var(--chart-text)', fontSize: 12 }}
                    axisLine={{ stroke: 'var(--chart-axis)' }}
                    tickLine={{ stroke: 'var(--chart-axis)' }}
                  />
                  <YAxis
                    tick={{ fill: 'var(--chart-text)', fontSize: 12 }}
                    axisLine={{ stroke: 'var(--chart-axis)' }}
                    tickLine={{ stroke: 'var(--chart-axis)' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: token.colorBgContainer,
                      borderColor: token.colorBorderSecondary,
                      borderRadius: 6,
                    }}
                    formatter={(value: number) => [`¥${value.toLocaleString()}`, t('dashboard.categoryValue')]}
                    cursor={{ fill: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)' }}
                  />
                  {/*
                    Bar: ≤ 24px wide, 4 px rounded data-end, square at the
                    baseline. Single series → no legend; title names the series.
                  */}
                  <Bar
                    dataKey="total_value"
                    fill={BAR_COLOR}
                    maxBarSize={24}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-400 dark:text-gray-500 py-10">
                {t('dashboard.noCategoryData')}
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* ---- Upcoming subscriptions ---- */}
      <Row gutter={16} className="mt-4">
        <Col xs={24}>
          <Card title={t('dashboard.upcomingSubscriptions')}>
            <Table
              dataSource={dashboard.upcoming_subscriptions || []}
              columns={upcomingCols}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* ---- Expiring-soon reminders ---- */}
      <Row gutter={16} className="mt-4">
        <Col xs={24}>
          <Card title={t('dashboard.expiringSoon')}>
            {remindersError ? (
              <Typography.Text type="danger">{t('dashboard.loadFailed')}</Typography.Text>
            ) : reminders && reminders.length > 0 ? (
              <List
                size="small"
                dataSource={reminders.slice(0, 5)}
                renderItem={(item: any) => (
                  <List.Item>
                    <List.Item.Meta
                      title={item.name}
                      description={`${t('subscriptions.nextRenewal')}: ${item.next_renewal} | ¥${item.custom_data?.value ?? 0}`}
                    />
                    <Tag color="orange">{t('dashboard.expiringSoon')}</Tag>
                  </List.Item>
                )}
              />
            ) : (
              <Typography.Text type="secondary">
                {t('dashboard.noExpiring', '暂无即将到期的订阅')}
              </Typography.Text>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
