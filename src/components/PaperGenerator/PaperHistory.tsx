import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Table, Tag, Space, Button, message, Popconfirm, Typography, Progress } from 'antd'
import { DeleteOutlined, EyeOutlined, FileTextOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchPapers, deletePaper, setCurrentPaper, Paper } from '@/store/slices/papersSlice'

const { Text } = Typography

interface PaperHistoryProps {
    onView: () => void
}

const PaperHistory: React.FC<PaperHistoryProps> = ({ onView }) => {
    const dispatch = useDispatch<AppDispatch>()
    const { papers, loading } = useSelector((state: RootState) => state.papers)

    useEffect(() => {
        dispatch(fetchPapers())
    }, [dispatch])

    const handleDelete = async (id: number) => {
        try {
            await dispatch(deletePaper(id)).unwrap()
            message.success('删除成功')
        } catch (error) {
            message.error('删除失败')
        }
    }

    const handleView = (record: Paper) => {
        dispatch(setCurrentPaper(record))
        onView()
    }

    const columns = [
        {
            title: '论文标题',
            dataIndex: 'title',
            key: 'title',
            width: '40%',
            ellipsis: true,
            render: (text: string) => (
                <Space>
                    <FileTextOutlined style={{ color: '#1890ff' }} />
                    <Text strong>{text}</Text>
                </Space>
            ),
        },
        {
            title: '质量评分',
            dataIndex: 'quality_score',
            key: 'quality_score',
            width: '20%',
            sorter: (a: Paper, b: Paper) => a.quality_score - b.quality_score,
            render: (score: number) => (
                <Progress
                    percent={score}
                    size="small"
                    status={score >= 80 ? 'success' : 'normal'}
                />
            ),
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: '15%',
            render: (status: string) => {
                let color = 'default'
                let label = status
                if (status === 'completed') { color = 'green'; label = '已完成'; }
                else if (status === 'processing') { color = 'blue'; label = '进行中'; }
                else if (status === 'error') { color = 'red'; label = '失败'; }
                return <Tag color={color}>{label}</Tag>
            },
        },
        {
            title: '生成时间',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 120,
            render: (date: string) => new Date(date).toLocaleDateString('zh-CN'),
        },
        {
            title: '操作',
            key: 'action',
            fixed: 'right' as const,
            width: 150,
            render: (_: any, record: Paper) => (
                <Space size="small">
                    <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleView(record)}
                        disabled={record.status !== 'completed'}
                        style={{ padding: '0 4px' }}
                    >
                        查看
                    </Button>
                    <Popconfirm
                        title="确定删除这篇论文吗？"
                        onConfirm={() => handleDelete(record.id)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button
                            type="link"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            style={{ padding: '0 4px' }}
                        >
                            删除
                        </Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ]

    return (
        <Table
            columns={columns}
            dataSource={papers}
            loading={loading}
            rowKey="id"
            pagination={{ pageSize: 8 }}
            scroll={{ x: 'max-content' }}
        />
    )
}

export default PaperHistory
