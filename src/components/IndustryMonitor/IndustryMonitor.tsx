import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Card, List, Tag, Button, Space, Typography, Empty, Select } from 'antd'
import { ReloadOutlined, LinkOutlined, ClockCircleOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchIndustryNews, refreshIndustryNews } from '@/store/slices/industrySlice'

const { Title, Text, Paragraph } = Typography

const IndustryMonitor: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { news, loading } = useSelector((state: RootState) => state.industry)
  const { topics } = useSelector((state: RootState) => state.topics)
  const [selectedTopicId, setSelectedTopicId] = React.useState<number | null>(null)

  useEffect(() => {
    dispatch(fetchIndustryNews())
    // Fetch topics for the dropdown
    import('@/store/slices/topicsSlice').then(({ fetchTopics }) => {
      dispatch(fetchTopics())
    })
  }, [dispatch])

  const handleRefresh = () => {
    if (selectedTopicId) {
      dispatch(refreshIndustryNews(selectedTopicId))
    }
  }

  const handleTopicChange = (value: number) => {
    setSelectedTopicId(value)
    // Optional: Fetch existing news for this topic when selected
    dispatch(fetchIndustryNews(value))
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>行业动态追踪</Title>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>选择研究选题：</Text>
          <Select
            style={{ width: 400 }}
            placeholder="请选择一个研究选题以获取相关动态"
            onChange={handleTopicChange}
            value={selectedTopicId}
          >
            {topics.map((topic) => (
              <Select.Option key={topic.id} value={topic.id}>
                {topic.title}
              </Select.Option>
            ))}
          </Select>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
            disabled={!selectedTopicId}
          >
            AI 实时搜索动态
          </Button>
        </Space>
      </Card>

      {news.length === 0 && !loading ? (
        <Empty description={selectedTopicId ? "暂无相关动态，点击搜索获取" : "请先选择一个选题"} />
      ) : (
        <List
          grid={{ gutter: 16, column: 1 }}
          dataSource={news}
          loading={loading}
          renderItem={(item) => (
            <List.Item>
              <Card
                hoverable
                title={
                  <Space>
                    <Text strong>{item.title}</Text>
                    <Tag color="blue">相关度: {(item.relevance_score * 100).toFixed(0)}%</Tag>
                  </Space>
                }
                extra={
                  item.url ? (
                    <a href={item.url} target="_blank" rel="noopener noreferrer">
                      <Button type="link" icon={<LinkOutlined />}>
                        查看原文
                      </Button>
                    </a>
                  ) : null
                }
              >
                <Paragraph ellipsis={{ rows: 3 }}>{item.content}</Paragraph>
                <Space wrap>
                  {item.keywords?.map((keyword) => (
                    <Tag key={keyword} color="geekblue">
                      {keyword}
                    </Tag>
                  ))}
                </Space>
                <div style={{ marginTop: 12 }}>
                  <Text type="secondary">
                    <ClockCircleOutlined /> 来源: {item.source} | 发布时间:{' '}
                    {new Date(item.published_at).toLocaleDateString('zh-CN')}
                  </Text>
                </div>
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  )
}

export default IndustryMonitor
