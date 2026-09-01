import { useEffect, useState, useMemo } from 'react'
import { Form, Input, Select, Button, Card, Spin, message } from 'antd'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import DynamicForm, { validateForm } from '../../components/DynamicForm'
import { useAssetTypes, useAssetType } from '../../api/hooks/asset-types'
import { useAsset, useCreateAsset, useUpdateAsset } from '../../api/hooks/assets'
import { useCategoriesByType } from '../../api/hooks/categories'

export default function AssetForm() {
  const { t } = useTranslation()
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const isEdit = !!id
  const navigate = useNavigate()
  const [form] = Form.useForm()

  // State
  const [selectedTypeId, setSelectedTypeId] = useState<number>(() => {
    const fromUrl = searchParams.get('type_id')
    return fromUrl ? Number(fromUrl) : 0
  })
  const [customValues, setCustomValues] = useState<Record<string, any>>({})
  const [customErrors, setCustomErrors] = useState<Record<string, string>>({})

  // Hooks
  const { data: assetTypes = [], isLoading: typesLoading } = useAssetTypes()
  const { data: assetType, isLoading: typeLoading } = useAssetType(selectedTypeId)
  const { data: categories = [], isLoading: catsLoading } = useCategoriesByType(selectedTypeId)
  const { data: existingAsset, isLoading: assetLoading } = useAsset(isEdit ? Number(id) : 0)
  const createMutation = useCreateAsset()
  const updateMutation = useUpdateAsset()

  // When editing, populate form from existing asset
  useEffect(() => {
    if (isEdit && existingAsset) {
      form.setFieldsValue({
        name: existingAsset.name,
        category_id: existingAsset.category_id,
      })
      setSelectedTypeId(existingAsset.type_id)
      setCustomValues(existingAsset.custom_data || {})
    }
  }, [isEdit, existingAsset, form])

  // When type changes in create mode, reset custom values and category
  const handleTypeChange = (typeId: number) => {
    setSelectedTypeId(typeId)
    setCustomValues({})
    setCustomErrors({})
    form.setFieldValue('category_id', undefined)
  }

  const handleCustomChange = (values: Record<string, any>) => {
    setCustomValues(values)
    // Clear errors on change
    setCustomErrors((prev) => {
      const next = { ...prev }
      for (const key of Object.keys(values)) {
        delete next[key]
      }
      return next
    })
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      // Validate dynamic form fields
      if (assetType?.field_config) {
        const errors = validateForm(assetType.field_config, customValues)
        if (Object.keys(errors).length > 0) {
          setCustomErrors(errors)
          return
        }
      }

      if (isEdit) {
        await updateMutation.mutateAsync({
          id: Number(id),
          name: values.name,
          category_id: values.category_id,
          custom_data: customValues,
        })
        message.success(t('assets.assetUpdated'))
      } else {
        await createMutation.mutateAsync({
          type_id: selectedTypeId,
          name: values.name,
          category_id: values.category_id,
          custom_data: customValues,
        })
        message.success(t('assets.assetCreated'))
      }
      navigate('/asset-management')
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message)
      }
    }
  }

  // Flatten categories for select
  const flatCategories = useMemo(() => {
    const result: { id: number; name: string }[] = []
    function walk(items: typeof categories) {
      for (const c of items) {
        result.push({ id: c.id, name: c.name })
        if (c.children) walk(c.children)
      }
    }
    walk(categories)
    return result
  }, [categories])

  // Loading states
  const isLoading = typesLoading || typeLoading || catsLoading || (isEdit && assetLoading)

  if (isLoading) {
    return (
      <div>
        <PageHeader title={isEdit ? t('assets.editAsset') : t('assets.createAsset')} />
        <div className="flex justify-center items-center py-20">
          <Spin size="large" />
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader title={isEdit ? t('assets.editAsset') : t('assets.createAsset')} />
      <Card className="max-w-2xl">
        <Form form={form} layout="vertical">
          {/* Asset Type - required for both modes */}
          <Form.Item
            label={t('assetManagement.type')}
            required
            validateStatus={!isEdit && !selectedTypeId ? undefined : undefined}
          >
            {isEdit ? (
              <Input
                value={assetType?.name || existingAsset?.asset_type?.name || ''}
                disabled
              />
            ) : (
              <Select
                placeholder={t('assetManagement.filterByType')}
                loading={typesLoading}
                value={selectedTypeId || undefined}
                onChange={handleTypeChange}
                showSearch
                optionFilterProp="label"
                options={assetTypes.map((at) => ({
                  value: at.id,
                  label: at.name,
                }))}
              />
            )}
          </Form.Item>

          {/* Name - required for both modes */}
          <Form.Item
            name="name"
            label={t('assets.name')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input />
          </Form.Item>

          {/* Category - depends on selected type */}
          {selectedTypeId > 0 && (
            <Form.Item
              name="category_id"
              label={t('assets.category')}
            >
              <Select
                placeholder={t('assets.selectCategory')}
                allowClear
                loading={catsLoading}
                showSearch
                optionFilterProp="label"
                options={flatCategories.map((c) => ({
                  value: c.id,
                  label: c.name,
                }))}
              />
            </Form.Item>
          )}

          {/* Dynamic Form - only when type is selected and has fields */}
          {selectedTypeId > 0 && assetType?.field_config?.fields?.length ? (
            <>
              <div className="border-t pt-4 mt-2 mb-2 font-medium">{t('assets.customFields')}</div>
              <DynamicForm
                fieldConfig={assetType.field_config}
                values={customValues}
                onChange={handleCustomChange}
                errors={customErrors}
              />
            </>
          ) : null}

          {/* Submit */}
          <Form.Item className="mt-4">
            <Button
              type="primary"
              onClick={handleSubmit}
              loading={createMutation.isPending || updateMutation.isPending}
            >
              {isEdit ? t('assets.saveChanges') : t('assets.createAsset')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
