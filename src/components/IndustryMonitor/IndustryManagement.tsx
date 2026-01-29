import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Table, Tag, Space, Button, Modal, Form, Input, message, InputNumber, Popconfirm, Typography } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, LinkOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import { addIndustryNews, updateIndustryNews, deleteIndustryNews, IndustryNews } from '@/store/slices/industrySlice'

const { TextArea } = Input
const { Text, Paragraph } = Typography

interface IndustryManagementProps {
    topicId: number | null
}

const IndustryManagement: React.FC<IndustryManagementProps> = ({ topicId }) => {
    const dispatch = useDispatch<AppDispatch>()
    const { news, loading } = useSelector((state: RootState) => state.industry)
    const [isModalVisible, setIsModalVisible] = useState(false)
    const [editingNews, setEditingNews] = useState<IndustryNews | null>(null)
    const [form] = Form.useForm()

    const handleAdd = () => {
        setEditingNews(null)
        form.resetFields()
        setIsModalVisible(true)
    }

    const handleEdit = (record: IndustryNews) => {
        setEditingNews(record)
        form.setFieldsValue({
            ...record,
            keywords: record.keywords.join(', '),
        })
        setIsModalVisible(true)
    }

    const handleDelete = async (id: number) => {
        try {
            await dispatch(deleteIndustryNews(id)).unwrap()
            message.success('删除成功')
        } catch (error) {
            message.error('删除失败')
        }
    }

    const handleFinish = async (values: any) => {
        const formattedValues = {
            ...values,
            topic_id: topicId,
            keywords: values.keywords ? values.keywords.split(',').map((k: string) => k.trim()) : [],
        }

        try {
            if (editingNews) {
                await dispatch(updateIndustryNews({ id: editingNews.id, data: formattedValues })).unwrap()
                message.success('更新成功')
            } else {
                await dispatch(addIndustryNews(formattedValues)).unwrap()
                message.success('添加成功')
            }
            setIsModalVisible(false)
        } catch (error) {
            message.error('操作失败')
        }
    }

    const columns = [
        {
            title: '标题',
            dataIndex: 'title',
            key: 'title',
            width: '30%',
            ellipsis: true,
        },
        {
            title: '来源',
            dataIndex: 'source',
            key: 'source',
            width: '15%',
        },
        {
            title: '相关度',
            dataIndex: 'relevance_score',
            key: 'relevance_score',
            width: '10%',
            render: (score: number) => <Tag color="blue">{(score * 100).toFixed(0)}%</Tag>,
        },
        {
            title: '发布时间',
            dataIndex: 'published_at',
            key: 'published_at',
            width: '15%',
            render: (date: string) => date ? new Date(date).toLocaleDateString('zh-CN') : '-',
        },
        {
            title: '操作',
            key: 'action',
            render: (_: any, record: IndustryNews) => (
                <Space size="middle">
                    <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
                    <Popconfirm title="确定删除吗？" onConfirm={() => handleDelete(record.id)}>
                        <Button danger icon={<DeleteOutlined />}>删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ]

    return (
        <div>
            <div style={{ marginBottom: 16, textAlign: 'right' }}>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleAdd}
                    disabled={!topicId}
                >
                    手动添加动态
                </Button>
            </div>

            <Table
                columns={columns}
                dataSource={news}
                loading={loading}
                rowKey="id"
                pagination={{ pageSize: 5 }}
                expandable={{
                    expandedRowRender: (record) => (
                        <div style={{ padding: '8px 24px', backgroundColor: '#fafafa', borderRadius: 4 }}>
                            <Text strong>动态摘要：</Text>
                            <Paragraph style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>{record.content}</Paragraph>
                            {record.url && (
                                <div style={{ marginTop: 8 }}>
                                    <a href={record.url} target="_blank" rel="noopener noreferrer">
                                        <Button type="link" icon={<LinkOutlined />} size="small" style={{ padding: 0 }}>
                                            查看原文链接
                                        </Button>
                                    </a>
                                </div>
                            )}
                        </div>
                    ),
                    rowExpandable: (record) => !!record.content,
                }}
            />

            <Modal
                title={editingNews ? '编辑动态' : '添加动态'}
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                onOk={() => form.submit()}
                width={700}
            >
                <Form form={form} layout="vertical" onFinish={handleFinish}>
                    <Form.Item name="title" label="标题" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="source" label="来源" rules={[{ required: true }]}>
                        <Input placeholder="例如：NVIDIA Blog, Reuters" />
                    </Form.Item>
                    <Form.Item name="url" label="原文链接">
                        <Input />
                    </Form.Item>
                    <Form.Item name="content" label="内容摘要" rules={[{ required: true }]}>
                        <TextArea rows={4} />
                    </Form.Item>
                    <Form.Item name="keywords" label="关键词 (逗号分隔)">
                        <Input />
                    </Form.Item>
                    <Form.Item name="relevance_score" label="相关度 (0.0 - 1.0)" initialValue={0.8}>
                        <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="published_at" label="发布时间 (YYYY-MM-DD)">
                        <Input placeholder="2024-01-29" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default IndustryManagement
