import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Table, Tag, Space, Button, Modal, Form, Input, message, InputNumber, Popconfirm, Typography, Divider } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, LinkOutlined, FileSearchOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import { addCompetitor, updateCompetitor, deleteCompetitor, Competitor } from '@/store/slices/competitorsSlice'

const { TextArea } = Input
const { Text, Paragraph } = Typography

interface CompetitorManagementProps {
    topicId: number | null
}

const CompetitorManagement: React.FC<CompetitorManagementProps> = ({ topicId }) => {
    const dispatch = useDispatch<AppDispatch>()
    const { competitors, loading } = useSelector((state: RootState) => state.competitors)
    const [isModalVisible, setIsModalVisible] = useState(false)
    const [editingComp, setEditingComp] = useState<Competitor | null>(null)
    const [form] = Form.useForm()

    const handleAdd = () => {
        setEditingComp(null)
        form.resetFields()
        setIsModalVisible(true)
    }

    const handleEdit = (record: Competitor) => {
        setEditingComp(record)
        form.setFieldsValue(record)
        setIsModalVisible(true)
    }

    const handleDelete = async (id: number) => {
        try {
            await dispatch(deleteCompetitor(id)).unwrap()
            message.success('删除成功')
        } catch (error) {
            message.error('删除失败')
        }
    }

    const handleFinish = async (values: any) => {
        const formattedValues = {
            ...values,
            topic_id: topicId,
        }

        try {
            if (editingComp) {
                await dispatch(updateCompetitor({ id: editingComp.id, data: formattedValues })).unwrap()
                message.success('更新成功')
            } else {
                await dispatch(addCompetitor(formattedValues)).unwrap()
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
            width: '35%',
            ellipsis: true,
        },
        {
            title: '作者',
            dataIndex: 'authors',
            key: 'authors',
            width: '20%',
            ellipsis: true,
        },
        {
            title: '引用数',
            dataIndex: 'citations',
            key: 'citations',
            width: '10%',
            sorter: (a: Competitor, b: Competitor) => a.citations - b.citations,
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
            render: (_: any, record: Competitor) => (
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
                    手动录入竞品
                </Button>
            </div>

            <Table
                columns={columns}
                dataSource={competitors}
                loading={loading}
                rowKey="id"
                pagination={{ pageSize: 5 }}
                expandable={{
                    expandedRowRender: (record) => (
                        <div style={{ padding: '16px 24px', backgroundColor: '#fafafa', borderRadius: 8 }}>
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <div>
                                    <Text strong><FileSearchOutlined /> 论文摘要：</Text>
                                    <Paragraph style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>{record.abstract || '暂无摘要内容'}</Paragraph>
                                </div>
                                {record.analysis && (
                                    <>
                                        <Divider style={{ margin: '8px 0' }} />
                                        <div>
                                            <Text strong style={{ color: '#1890ff' }}>🤖 AI 深度分析：</Text>
                                            <Paragraph style={{ marginTop: 8, whiteSpace: 'pre-wrap', color: '#555' }}>{record.analysis}</Paragraph>
                                        </div>
                                    </>
                                )}
                                {record.url && (
                                    <div style={{ marginTop: 8 }}>
                                        <a href={record.url} target="_blank" rel="noopener noreferrer">
                                            <Button type="link" icon={<LinkOutlined />} size="small" style={{ padding: 0 }}>
                                                查阅在线原文
                                            </Button>
                                        </a>
                                    </div>
                                )}
                            </Space>
                        </div>
                    ),
                    rowExpandable: (record) => !!(record.abstract || record.analysis),
                }}
            />

            <Modal
                title={editingComp ? '编辑竞品' : '录入竞品'}
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                onOk={() => form.submit()}
                width={700}
            >
                <Form form={form} layout="vertical" onFinish={handleFinish}>
                    <Form.Item name="title" label="标题" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="authors" label="作者" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="source" label="来源 (Journal/Conference)" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="url" label="原文链接">
                        <Input />
                    </Form.Item>
                    <Form.Item name="abstract" label="摘要" rules={[{ required: true }]}>
                        <TextArea rows={4} />
                    </Form.Item>
                    <Form.Item name="citations" label="引用数" initialValue={0}>
                        <InputNumber min={0} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="published_at" label="发布时间 (YYYY-MM-DD)">
                        <Input placeholder="2024-01-29" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default CompetitorManagement
