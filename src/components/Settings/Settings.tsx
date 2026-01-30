import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Tag,
  message,
  Popconfirm,
  Typography,
  Alert,
  Tooltip,
  Result,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ApiOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import {
  fetchConfigs,
  fetchPrimaryConfig,
  createConfig,
  updateConfig,
  deleteConfig,
  setPrimaryConfig,
  testConnection,
  clearTestResult,
  LLMConfig,
  LLMConfigCreate,
  LLMConfigUpdate,
} from '@/store/slices/llmConfigSlice'

const { Title, Text } = Typography
const { Option } = Select

const Settings: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { configs, primaryConfig, loading, error, testResult, testing } = useSelector(
    (state: RootState) => state.llmConfig
  )

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null)
  const [form] = Form.useForm()

  // 加载配置列表
  useEffect(() => {
    dispatch(fetchConfigs())
    dispatch(fetchPrimaryConfig())
  }, [dispatch])

  // 显示错误消息
  useEffect(() => {
    if (error) {
      message.error(error)
    }
  }, [error])

  // 打开新建/编辑弹窗
  const handleOpenModal = (config?: LLMConfig) => {
    if (config) {
      setEditingConfig(config)
      form.setFieldsValue({
        name: config.name,
        provider: config.provider,
        base_url: config.base_url,
        api_key: config.api_key, // 直接显示 API Key
        default_model: config.default_model,
        max_tokens: config.max_tokens,
        timeout: config.timeout,
      })
    } else {
      setEditingConfig(null)
      form.resetFields()
      // 设置默认值
      form.setFieldsValue({
        provider: 'anthropic',
        max_tokens: 4096,
        timeout: 120,
      })
    }
    dispatch(clearTestResult())
    setIsModalOpen(true)
  }

  // 关闭弹窗
  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingConfig(null)
    form.resetFields()
    dispatch(clearTestResult())
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingConfig) {
        // 编辑模式 - 只发送有变化的字段
        const updateData: LLMConfigUpdate = {}
        if (values.name !== editingConfig.name) updateData.name = values.name
        if (values.provider !== editingConfig.provider) updateData.provider = values.provider
        if (values.base_url !== editingConfig.base_url) updateData.base_url = values.base_url
        if (values.api_key) updateData.api_key = values.api_key // 只有填写了才更新
        if (values.default_model !== editingConfig.default_model) updateData.default_model = values.default_model
        if (values.max_tokens !== editingConfig.max_tokens) updateData.max_tokens = values.max_tokens
        if (values.timeout !== editingConfig.timeout) updateData.timeout = values.timeout
        
        await dispatch(updateConfig({ id: editingConfig.id, data: updateData })).unwrap()
        message.success('配置更新成功')
      } else {
        // 新建模式
        const createData: LLMConfigCreate = {
          name: values.name,
          provider: values.provider,
          base_url: values.base_url,
          api_key: values.api_key,
          default_model: values.default_model,
          max_tokens: values.max_tokens,
          timeout: values.timeout,
        }
        await dispatch(createConfig(createData)).unwrap()
        message.success('配置创建成功')
      }
      
      handleCloseModal()
      dispatch(fetchConfigs())
      dispatch(fetchPrimaryConfig())
    } catch (err: any) {
      message.error(err.message || '操作失败')
    }
  }

  // 删除配置
  const handleDelete = async (id: number) => {
    try {
      await dispatch(deleteConfig(id)).unwrap()
      message.success('配置已删除')
      dispatch(fetchPrimaryConfig())
    } catch (err: any) {
      message.error(err.message || '删除失败')
    }
  }

  // 设置为主配置
  const handleSetPrimary = async (id: number) => {
    try {
      await dispatch(setPrimaryConfig(id)).unwrap()
      message.success('已设置为主模型')
    } catch (err: any) {
      message.error(err.message || '设置失败')
    }
  }

  // 测试连接
  const handleTestConnection = async () => {
    const values = form.getFieldsValue()
    if (!values.base_url || !values.api_key) {
      message.warning('请先填写 Base URL 和 API Key')
      return
    }
    
    await dispatch(testConnection({
      base_url: values.base_url,
      api_key: values.api_key,
      model: values.default_model || 'claude-haiku-4-5',
    }))
  }

  // 表格列定义
  const columns = [
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: LLMConfig) => (
        <Space>
          <span>{name}</span>
          {record.is_primary && <Tag color="green">主模型</Tag>}
        </Space>
      ),
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => (
        <Tag color="blue">{provider}</Tag>
      ),
    },
    {
      title: 'Base URL',
      dataIndex: 'base_url',
      key: 'base_url',
      ellipsis: true,
      render: (url: string) => (
        <Tooltip title={url}>
          <Text copyable={{ text: url }} style={{ maxWidth: 200 }}>
            {url.length > 30 ? url.substring(0, 30) + '...' : url}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '默认模型',
      dataIndex: 'default_model',
      key: 'default_model',
    },
    {
      title: 'Max Tokens',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: LLMConfig) => (
        <Space size="small">
          {!record.is_primary && (
            <Tooltip title="设为主模型">
              <Button
                type="link"
                icon={<CheckCircleOutlined />}
                onClick={() => handleSetPrimary(record.id)}
              />
            </Tooltip>
          )}
          <Tooltip title="编辑">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除此配置吗？"
            description={record.is_primary ? "这是当前主模型，删除后将自动切换到其他配置" : undefined}
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '0' }}>
      <Title level={3}>
        <SettingOutlined /> 模型配置
      </Title>
      
      {/* 当前主模型状态卡片 */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>当前主模型：</Text>
          {primaryConfig ? (
            <Space>
              <Tag color="green" icon={<CheckCircleOutlined />}>
                {primaryConfig.name}
              </Tag>
              <Text type="secondary">
                {primaryConfig.default_model} @ {primaryConfig.base_url}
              </Text>
            </Space>
          ) : (
            <Alert
              message="使用默认配置"
              description="尚未添加自定义模型配置，系统将使用默认配置。"
              type="info"
              showIcon
            />
          )}
        </Space>
      </Card>

      {/* 配置列表 */}
      <Card
        title="模型配置列表"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            新增配置
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={false}
          locale={{
            emptyText: (
              <Result
                icon={<ApiOutlined style={{ color: '#999' }} />}
                title="暂无配置"
                subTitle="点击上方按钮添加第一个模型配置"
              />
            ),
          }}
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingConfig ? '编辑配置' : '新增配置'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        width={600}
        confirmLoading={loading}
        footer={[
          <Button key="test" icon={<ThunderboltOutlined />} onClick={handleTestConnection} loading={testing}>
            测试连接
          </Button>,
          <Button key="cancel" onClick={handleCloseModal}>
            取消
          </Button>,
          <Button key="submit" type="primary" onClick={handleSubmit} loading={loading}>
            {editingConfig ? '保存' : '创建'}
          </Button>,
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="例如：DeepSeek AI、OpenAI GPT-4" />
          </Form.Item>

          <Form.Item
            name="provider"
            label="提供商"
            rules={[{ required: true, message: '请选择提供商' }]}
          >
            <Select>
              <Option value="anthropic">Anthropic</Option>
              <Option value="openai">OpenAI</Option>
              <Option value="deepseek">DeepSeek</Option>
              <Option value="custom">自定义</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="base_url"
            label="Base URL"
            rules={[{ required: true, message: '请输入 Base URL' }]}
            extra="API 端点地址，例如：http://127.0.0.1:8045"
          >
            <Input placeholder="http://127.0.0.1:8045" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: true, message: '请输入 API Key' }]}
          >
            <Input placeholder="sk-xxxxxxxx" />
          </Form.Item>

          <Form.Item
            name="default_model"
            label="默认模型"
            rules={[{ required: true, message: '请输入默认模型' }]}
            extra="例如：claude-haiku-4-5、gpt-4、deepseek-chat"
          >
            <Input placeholder="claude-haiku-4-5" />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item
              name="max_tokens"
              label="Max Tokens"
              rules={[{ required: true, message: '请输入' }]}
            >
              <InputNumber min={100} max={100000} style={{ width: 150 }} />
            </Form.Item>

            <Form.Item
              name="timeout"
              label="超时时间 (秒)"
              rules={[{ required: true, message: '请输入' }]}
            >
              <InputNumber min={10} max={600} style={{ width: 150 }} />
            </Form.Item>
          </Space>

          {/* 测试结果显示 */}
          {testResult && (
            <Alert
              message={testResult.success ? '连接成功' : '连接失败'}
              description={
                <Space direction="vertical">
                  <Text>{testResult.message}</Text>
                  {testResult.response_time_ms && (
                    <Text type="secondary">响应时间: {testResult.response_time_ms}ms</Text>
                  )}
                </Space>
              }
              type={testResult.success ? 'success' : 'error'}
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default Settings
