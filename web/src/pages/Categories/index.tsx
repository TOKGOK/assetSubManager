import { useState, useMemo, type ReactNode } from 'react'
import { Tree, Card, Button, Modal, Form, Input, Select, Tag, Popconfirm,
         Table, Space, message, Empty, Spin } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import { useAssetTypes } from '../../api/hooks/asset-types'
import {
  useCategoriesByType,
  useCreateCategoryByType,
  useUpdateCategory,
  useDeleteCategory,
} from '../../api/hooks/categories'
import type { Category } from '../../types'

export default function Categories() {
  const { t } = useTranslation()

  // Asset types
  const { data: assetTypes = [], isLoading: typesLoading } = useAssetTypes()
  const [selectedTypeId, setSelectedTypeId] = useState<number>(0)

  // Auto-select first type when types load
  const effectiveTypeId = useMemo(() => {
    if (selectedTypeId > 0 && assetTypes.some(t => t.id === selectedTypeId)) {
      return selectedTypeId
    }
    return assetTypes.length > 0 ? assetTypes[0].id : 0
  }, [selectedTypeId, assetTypes])

  // Categories for selected type
  const { data: effectiveCategories = [], isLoading: effectiveCatsLoading } =
    useCategoriesByType(effectiveTypeId)
  const createCat = useCreateCategoryByType(effectiveTypeId)
  const updateCat = useUpdateCategory()
  const deleteCat = useDeleteCategory()

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingCat, setEditingCat] = useState<Category | null>(null)
  const [form] = Form.useForm()

  const selectedCat = useMemo(
    () => findCategory(effectiveCategories, selectedId),
    [effectiveCategories, selectedId],
  )
  const isDefaultSelected = selectedCat?.is_default === true

  // Reset selection when type changes
  const handleTypeChange = (typeId: number) => {
    setSelectedTypeId(typeId)
    setSelectedId(null)
  }

  function toTreeData(cats: Category[]): { key: number; title: ReactNode; children?: any[] }[] {
    return cats.map(c => ({
      key: c.id,
      title: (
        <span className="inline-flex items-center gap-1">
          <span>{c.name}</span>
          {c.is_default && (
            <Tag color="default" style={{ marginLeft: 2, fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
              {t('categories.default')}
            </Tag>
          )}
        </span>
      ),
      children: c.children?.length ? toTreeData(c.children) : undefined,
    }))
  }

  const fieldColumns = [
    { title: t('categories.fieldName'), dataIndex: 'field_name', key: 'field_name' },
    { title: t('categories.fieldType'), dataIndex: 'field_type', key: 'field_type' },
    {
      title: t('categories.isRequired'), dataIndex: 'required', key: 'required',
      render: (v: boolean) => v ? <Tag color="red">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
    },
  ]

  async function handleCreate(values: { name: string; icon?: string; description?: string; parent_id?: number | null }) {
    await createCat.mutateAsync(values)
    message.success(t('categories.categoryCreated'))
    setModalOpen(false)
    setEditingCat(null)
    form.resetFields()
  }

  async function handleUpdate(values: { name: string; icon?: string; description?: string; parent_id?: number | null }) {
    if (!editingCat) return
    await updateCat.mutateAsync({ id: editingCat.id, ...values })
    message.success(t('categories.categoryUpdated'))
    setModalOpen(false)
    setEditingCat(null)
    form.resetFields()
  }

  function openCreateModal(parentId?: number | null) {
    setEditingCat(null)
    form.resetFields()
    if (parentId !== undefined) {
      form.setFieldsValue({ parent_id: parentId })
    }
    setModalOpen(true)
  }

  function openEditModal(cat: Category) {
    setEditingCat(cat)
    form.setFieldsValue({
      name: cat.name,
      icon: cat.icon,
      description: cat.description,
      parent_id: cat.parent_id,
    })
    setModalOpen(true)
  }

  async function handleDelete() {
    if (!selectedId) return
    try {
      await deleteCat.mutateAsync(selectedId)
      message.success(t('categories.categoryDeleted'))
      setSelectedId(null)
    } catch { /* error handled by interceptor */ }
  }

  // Build parent options for select (exclude current and its descendants)
  const parentOptions = useMemo(() => {
    const opts: { value: number | null; label: string }[] = [
      { value: null, label: t('categories.rootCategory') },
    ]
    function walk(cats: Category[], prefix = '') {
      for (const c of cats) {
        if (selectedId && c.id === selectedId) continue
        opts.push({ value: c.id, label: `${prefix}${c.name}` })
        if (c.children?.length) walk(c.children, `${prefix}  `)
      }
    }
    walk(effectiveCategories)
    return opts
  }, [effectiveCategories, selectedId, t])

  const loading = effectiveTypeId > 0 && effectiveCatsLoading

  return (
    <div>
      <PageHeader
        title={t('nav.categories')}
        extra={
          effectiveTypeId > 0 && (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openCreateModal()}>
              {t('categories.createCategory')}
            </Button>
          )
        }
      />

      {/* Asset Type Selector */}
      <div className="mb-4">
        <Space>
          <span className="font-medium">{t('categories.assetType')}:</span>
          <Select
            style={{ width: 240 }}
            placeholder={t('categories.selectAssetType')}
            value={effectiveTypeId || undefined}
            onChange={handleTypeChange}
            loading={typesLoading}
            options={assetTypes.map(at => ({
              value: at.id,
              label: (
                <Space>
                  {at.icon && <span>{at.icon}</span>}
                  <span>{at.name}</span>
                </Space>
              ),
            }))}
          />
        </Space>
      </div>

      {!effectiveTypeId ? (
        <Empty description={t('categories.noAssetTypes')} />
      ) : (
        <Spin spinning={loading}>
          <div className="flex gap-4">
            <Card className="w-72 shrink-0">
              {effectiveCategories.length > 0 ? (
                <Tree
                  treeData={toTreeData(effectiveCategories)}
                  onSelect={(keys) => keys.length > 0 && setSelectedId(keys[0] as number)}
                  selectedKeys={selectedId ? [selectedId] : []}
                  defaultExpandAll
                />
              ) : (
                <Empty description={t('categories.noCategories')} />
              )}
            </Card>

            <Card className="flex-1">
              {selectedCat ? (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <Space>
                      <span className="text-lg font-bold">{selectedCat.name}</span>
                      {selectedCat.icon && <span>{selectedCat.icon}</span>}
                      {isDefaultSelected && (
                        <Tag color="default">{t('categories.default')}</Tag>
                      )}
                    </Space>
                    <Space>
                      <Button
                        type="link"
                        icon={<PlusOutlined />}
                        onClick={() => openCreateModal(selectedCat.id)}
                      >
                        {t('categories.createSubCategory')}
                      </Button>
                      <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => openEditModal(selectedCat)}
                      >
                        {t('common.edit')}
                      </Button>
                      {isDefaultSelected ? (
                        <Button type="link" danger disabled title={t('categories.cannotDeleteDefault')}>
                          {t('common.delete')}
                        </Button>
                      ) : (
                        <Popconfirm title={t('common.confirmDelete')} onConfirm={handleDelete}>
                          <Button type="link" danger>{t('common.delete')}</Button>
                        </Popconfirm>
                      )}
                    </Space>
                  </div>
                  {selectedCat.description && (
                    <p className="text-gray-500 dark:text-gray-400 mb-4">{selectedCat.description}</p>
                  )}

                  {selectedCat.fields && selectedCat.fields.length > 0 && (
                    <>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{t('categories.customFields')}</span>
                      </div>
                      <Table
                        dataSource={selectedCat.fields}
                        columns={fieldColumns}
                        rowKey="id"
                        size="small"
                        pagination={false}
                      />
                    </>
                  )}
                </div>
              ) : (
                <Empty description={t('categories.selectCategory')} />
              )}
            </Card>
          </div>
        </Spin>
      )}

      {/* Create / Edit Modal */}
      <Modal
        title={editingCat ? t('categories.editCategory') : t('categories.createCategory')}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); setEditingCat(null); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createCat.isPending || updateCat.isPending}
      >
        <Form form={form} layout="vertical" onFinish={editingCat ? handleUpdate : handleCreate}>
          <Form.Item name="name" label={t('common.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="parent_id" label={t('categories.parentCategory')}>
            <Select
              allowClear
              placeholder={t('categories.rootCategory')}
              options={parentOptions}
            />
          </Form.Item>
          <Form.Item name="icon" label={t('categories.icon')}>
            <Input placeholder={t('categories.iconPlaceholder')} />
          </Form.Item>
          <Form.Item name="description" label={t('categories.description')}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function findCategory(cats: Category[], id: number | null): Category | undefined {
  if (!id) return undefined
  for (const c of cats) {
    if (c.id === id) return c
    if (c.children) {
      const found = findCategory(c.children, id)
      if (found) return found
    }
  }
  return undefined
}
