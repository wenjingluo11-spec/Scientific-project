import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Card, Select, List, Tag, Button, Space, Typography, Divider } from 'antd'
import { SearchOutlined, BarChartOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchCompetitors, analyzeCompetitor } from '@/store/slices/competitorsSlice'
import { fetchTopics } from '@/store/slices/topicsSlice'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

const CompetitorAnalysis: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { topics } = useSelector((state: RootState) => state.topics)
  const { competitors, loading } = useSelector((state: RootState) => state.competitors)
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null)

  useEffect(() => {
    dispatch(fetchTopics())
  }, [dispatch])

  const handleSearch = () => {
    if (selectedTopicId) {
      dispatch(fetchCompetitors(selectedTopicId))
    }
  }

  const handleAnalyze = (competitorId: number) => {
    dispatch(analyzeCompetitor(competitorId))
  }

  return (
    <div>
      <Title level={3}>竞品分析系统</Title>
      <Paragraph>
        选择研究选题，系统将自动搜索并分析同领域的相关论文。
      </Paragraph>

      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>选择选题：</Text>
          <Select
            style={{ width: 400 }}
            placeholder="请选择一个研究选题"
            onChange={(value) => setSelectedTopicId(value)}
            value={selectedTopicId}
          >
            {topics.map((topic) => (
              <Option key={topic.id} value={topic.id}>
                {topic.title}
              </Option>
            ))}
          </Select>
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSearch}
            disabled={!selectedTopicId}
            loading={loading}
          >
            搜索竞品
          </Button>
        </Space>
      </Card>

      <List
        grid={{ gutter: 16, column: 1 }}
        dataSource={competitors}
        loading={loading}
        renderItem={(item) => (
          <List.Item>
            <Card
              title={
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>{item.title}</Text>
                  <Space wrap>
                    <Tag color="orange">引用数: {item.citations}</Tag>
                    <Tag color="blue">来源: {item.source}</Tag>
                    <Text type="secondary">
                      发布时间: {new Date(item.published_at).toLocaleDateString('zh-CN')}
                    </Text>
                  </Space>
                </Space>
              }
              extra={
                <Space>
                  <Button
                    icon={<BarChartOutlined />}
                    onClick={() => handleAnalyze(item.id)}
                  >
                    AI 分析
                  </Button>
                  {item.url && (
                    <Button type="link" href={item.url} target="_blank">
                      查看原文
                    </Button>
                  )}
                </Space>
              }
            >
              <Paragraph>
                <Text strong>作者：</Text> {item.authors}
              </Paragraph>
              <Paragraph ellipsis={{ rows: 3, expandable: true }}>
                <Text strong>摘要：</Text> {item.abstract}
              </Paragraph>
              {item.analysis && (
                <>
                  <Divider />
                  <div>
                    <Text strong>AI 分析结果：</Text>
                    <Paragraph style={{ marginTop: 12, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                      {item.analysis}
                    </Paragraph>
                  </div>
                </>
              )}
            </Card>
          </List.Item>
        )}
      />
    </div>
  )
}

export default CompetitorAnalysis
