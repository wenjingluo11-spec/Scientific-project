import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Table, Tag, Space, Button, message, Popconfirm, Typography, Progress, Popover } from 'antd'
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
            title: '质量评分 (ICLR/NeurIPS)',
            dataIndex: 'quality_score',
            key: 'quality_score',
            width: 220,
            sorter: (a: Paper, b: Paper) => a.quality_score - b.quality_score,
            render: (score: number, record: Paper) => {
                let color = '#ff4d4f'; // Reject
                let label = 'Strong Reject';
                if (score >= 8.5) { color = '#722ed1'; label = 'Strong Accept'; }
                else if (score >= 6.5) { color = '#52c41a'; label = 'Accept'; }
                else if (score >= 5.0) { color = '#faad14'; label = 'Borderline'; }
                else if (score >= 3.0) { color = '#ff7a45'; label = 'Weak Reject'; }

                const detailedInfo = record.detailed_scores ? (
                    <div style={{ width: 200, padding: '8px 0' }}>
                        <Text strong style={{ display: 'block', marginBottom: 12 }}>维度评分详情</Text>
                        {[
                            { label: '创新性 (Novelty)', val: record.detailed_scores.novelty, color: '#722ed1' },
                            { label: '质量 (Quality)', val: record.detailed_scores.quality, color: '#2f54eb' },
                            { label: '清晰度 (Clarity)', val: record.detailed_scores.clarity, color: '#13c2c2' },
                            { label: '综合 (Total)', val: record.detailed_scores.total, color: '#faad14' }
                        ].map(d => (
                            <div key={d.label} style={{ marginBottom: 8 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: 2 }}>
                                    <Text type="secondary">{d.label}</Text>
                                    <Text strong>{d.val?.toFixed(1) || '0.0'}</Text>
                                </div>
                                <Progress percent={(d.val || 0) * 10} size="small" showInfo={false} strokeColor={d.color} />
                            </div>
                        ))}
                    </div>
                ) : null;

                return (
                    <Popover content={detailedInfo} title="ICLR/NeurIPS 评分维度详情">
                        <div style={{ minWidth: 160, cursor: 'pointer' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
                                <Text strong style={{ color, fontSize: '16px' }}>{score.toFixed(1)}</Text>
                                <Tag color={color} style={{ margin: 0, fontSize: '10px', borderRadius: '10px' }}>{label}</Tag>
                            </div>
                            {record.detailed_scores ? (
                                <div style={{ display: 'flex', gap: '4px', marginBottom: 4 }}>
                                    {[
                                        { k: 'N', v: record.detailed_scores.novelty, c: '#722ed1' },
                                        { k: 'Q', v: record.detailed_scores.quality, c: '#2f54eb' },
                                        { k: 'C', v: record.detailed_scores.clarity, c: '#13c2c2' }
                                    ].map(item => (
                                        <Tag key={item.k} style={{
                                            margin: 0,
                                            fontSize: '9px',
                                            padding: '0 4px',
                                            lineHeight: '14px',
                                            background: 'transparent',
                                            border: `1px solid ${item.c}44`,
                                            color: item.c
                                        }}>
                                            {item.k}: {item.v?.toFixed(1)}
                                        </Tag>
                                    ))}
                                </div>
                            ) : (
                                <Progress
                                    percent={score * 10}
                                    size="small"
                                    showInfo={false}
                                    strokeColor={color}
                                />
                            )}
                        </div>
                    </Popover>
                )
            },
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
