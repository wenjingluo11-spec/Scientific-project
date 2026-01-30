import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Table, Tag, Space, Button, message, Typography, Progress, Popover, Drawer, Divider, Card } from 'antd'
import { EyeOutlined, FileTextOutlined, DownloadOutlined, FilePdfOutlined, FileMarkdownOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchPapers, Paper } from '@/store/slices/papersSlice'

const { Text, Title } = Typography

const PaperHistory: React.FC = () => {
    const dispatch = useDispatch<AppDispatch>()
    const { papers, loading } = useSelector((state: RootState) => state.papers)
    
    // Drawer state
    const [drawerVisible, setDrawerVisible] = useState(false)
    const [viewingPaper, setViewingPaper] = useState<Paper | null>(null)

    useEffect(() => {
        dispatch(fetchPapers())
    }, [dispatch])



    const handleView = (record: Paper) => {
        setViewingPaper(record)
        setDrawerVisible(true)
    }

    const handleExportMarkdown = (record: Paper) => {
        if (!record.content) {
            message.warning('该论文暂无内容可导出')
            return
        }

        if (window.electronAPI) {
            window.electronAPI.saveFile(`${record.title}.md`, record.content)
                .then((result: { success: boolean }) => {
                    if (result.success) message.success('Markdown 导出成功！')
                })
        } else {
            // Web fallback
            const blob = new Blob([record.content], { type: 'text/markdown' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${record.title}.md`
            a.click()
            URL.revokeObjectURL(url)
            message.success('Markdown 导出成功！')
        }
    }

    const handleExportPDF = async (record: Paper) => {
        if (!record.content) {
            message.warning('该论文暂无内容可导出')
            return
        }

        message.loading({ content: '正在生成 PDF...', key: 'pdf-export' })

        try {
            // Create a hidden iframe for printing
            const printFrame = document.createElement('iframe')
            printFrame.style.position = 'absolute'
            printFrame.style.width = '0'
            printFrame.style.height = '0'
            printFrame.style.border = 'none'
            document.body.appendChild(printFrame)

            const printDoc = printFrame.contentDocument || printFrame.contentWindow?.document
            if (!printDoc) {
                throw new Error('无法创建打印文档')
            }

            // Simple markdown to HTML conversion for PDF
            const htmlContent = record.content
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
                .replace(/\*(.*)\*/gim, '<em>$1</em>')
                .replace(/\n/gim, '<br>')

            printDoc.open()
            printDoc.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>${record.title}</title>
                    <style>
                        body { 
                            font-family: 'Times New Roman', serif; 
                            padding: 40px; 
                            line-height: 1.6;
                            max-width: 800px;
                            margin: 0 auto;
                        }
                        h1 { font-size: 24px; margin-bottom: 20px; text-align: center; }
                        h2 { font-size: 18px; margin-top: 24px; margin-bottom: 12px; }
                        h3 { font-size: 16px; margin-top: 16px; margin-bottom: 8px; }
                        p { text-align: justify; }
                        @media print {
                            body { padding: 20px; }
                        }
                    </style>
                </head>
                <body>
                    <h1>${record.title}</h1>
                    ${htmlContent}
                </body>
                </html>
            `)
            printDoc.close()

            // Wait for content to load, then print
            setTimeout(() => {
                printFrame.contentWindow?.print()
                document.body.removeChild(printFrame)
                message.success({ content: 'PDF 导出窗口已打开，请选择保存位置', key: 'pdf-export' })
            }, 500)
        } catch (error) {
            message.error({ content: 'PDF 导出失败', key: 'pdf-export' })
            console.error('PDF export error:', error)
        }
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
            width: '12%',
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
                    <Popover
                        content={
                            <Space direction="vertical" size="small">
                                <Button
                                    type="text"
                                    size="small"
                                    icon={<FileMarkdownOutlined />}
                                    onClick={() => handleExportMarkdown(record)}
                                    disabled={!record.content}
                                    style={{ width: '100%', textAlign: 'left' }}
                                >
                                    Markdown (.md)
                                </Button>
                                <Button
                                    type="text"
                                    size="small"
                                    icon={<FilePdfOutlined />}
                                    onClick={() => handleExportPDF(record)}
                                    disabled={!record.content}
                                    style={{ width: '100%', textAlign: 'left' }}
                                >
                                    PDF (.pdf)
                                </Button>
                            </Space>
                        }
                        trigger="click"
                        placement="bottomRight"
                    >
                        <Button
                            type="link"
                            size="small"
                            icon={<DownloadOutlined />}
                            disabled={record.status !== 'completed' || !record.content}
                            style={{ padding: '0 4px' }}
                        >
                            导出
                        </Button>
                    </Popover>
                </Space>
            ),
        },
    ]

    return (
        <>
            <Table
                columns={columns}
                dataSource={papers}
                loading={loading}
                rowKey="id"
                pagination={{ pageSize: 8 }}
                scroll={{ x: 'max-content' }}
            />

            {/* Paper Detail Drawer */}
            <Drawer
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, maxWidth: 'calc(50vw - 350px)' }}>
                        <FileTextOutlined style={{ color: '#1890ff', flexShrink: 0 }} />
                        <span style={{ 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis', 
                            whiteSpace: 'nowrap',
                            display: 'block'
                        }}>
                            {viewingPaper?.title}
                        </span>
                    </div>
                }
                placement="right"
                width="50vw"
                height="100vh"
                open={drawerVisible}
                onClose={() => setDrawerVisible(false)}
                styles={{
                    body: { 
                        padding: 24,
                        height: 'calc(100vh)',
                        overflow: 'auto'
                    },
                    wrapper: {
                        height: '100vh',
                        
                    }
                }}
                extra={
                    <Space>
                        <Button
                            icon={<FileMarkdownOutlined />}
                            onClick={() => viewingPaper && handleExportMarkdown(viewingPaper)}
                            disabled={!viewingPaper?.content}
                        >
                            导出 Markdown
                        </Button>
                        <Button
                            type="primary"
                            icon={<FilePdfOutlined />}
                            onClick={() => viewingPaper && handleExportPDF(viewingPaper)}
                            disabled={!viewingPaper?.content}
                        >
                            导出 PDF
                        </Button>
                    </Space>
                }
            >
                {viewingPaper && (
                    <div>
                        {/* Paper Info Header */}
                        <Card size="small" style={{ marginBottom: 24, background: '#fafafa' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
                                <div>
                                    <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>创建时间</Text>
                                    <Text>{new Date(viewingPaper.created_at).toLocaleString('zh-CN')}</Text>
                                </div>
                                <div>
                                    <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>状态</Text>
                                    <Tag color={viewingPaper.status === 'completed' ? 'green' : 'blue'}>
                                        {viewingPaper.status === 'completed' ? '已完成' : '进行中'}
                                    </Tag>
                                </div>
                                <div>
                                    <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>综合评分</Text>
                                    <Title level={3} style={{ margin: 0, color: viewingPaper.quality_score >= 8.5 ? '#722ed1' : viewingPaper.quality_score >= 6.5 ? '#52c41a' : '#faad14' }}>
                                        {viewingPaper.quality_score.toFixed(1)}
                                    </Title>
                                </div>
                                {viewingPaper.detailed_scores && (
                                    <div style={{ flex: 1, minWidth: 300 }}>
                                        <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 8 }}>维度评分</Text>
                                        <div style={{ display: 'flex', gap: 16 }}>
                                            {[
                                                { label: '创新性', key: 'novelty', color: '#722ed1' },
                                                { label: '质量', key: 'quality', color: '#2f54eb' },
                                                { label: '清晰度', key: 'clarity', color: '#13c2c2' }
                                            ].map(item => (
                                                <div key={item.key} style={{ textAlign: 'center' }}>
                                                    <div style={{ fontSize: 11, color: '#8c8c8c', marginBottom: 2 }}>{item.label}</div>
                                                    <div style={{ fontSize: 16, fontWeight: 'bold', color: item.color }}>
                                                        {(viewingPaper.detailed_scores as any)[item.key]?.toFixed(1) || '0.0'}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </Card>

                        {/* Abstract */}
                        {viewingPaper.abstract && (
                            <>
                                <Title level={5} style={{ marginBottom: 8 }}>摘要</Title>
                                <Card size="small" style={{ marginBottom: 24, background: '#f9f9f9' }}>
                                    <Text>{viewingPaper.abstract}</Text>
                                </Card>
                            </>
                        )}

                        <Divider />

                        {/* Paper Content */}
                        <Title level={5} style={{ marginBottom: 16 }}>论文正文</Title>
                        <div style={{ 
                            border: '1px solid #f0f0f0', 
                            borderRadius: 8, 
                            padding: 24,
                            background: '#fff'
                        }}>
                            <ReactMarkdown>{viewingPaper.content || '暂无内容'}</ReactMarkdown>
                        </div>
                    </div>
                )}
            </Drawer>
        </>
    )
}

export default PaperHistory
