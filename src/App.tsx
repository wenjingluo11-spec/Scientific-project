import React, { useState } from 'react'
import { Layout, Menu, theme } from 'antd'
import {
  SearchOutlined,
  FileTextOutlined,
  LineChartOutlined,
  FundProjectionScreenOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import TopicSearch from './components/TopicSearch/TopicSearch'
import PaperGenerator from './components/PaperGenerator/PaperGenerator'
import IndustryMonitor from './components/IndustryMonitor/IndustryMonitor'
import CompetitorAnalysis from './components/CompetitorAnalysis/CompetitorAnalysis'

const { Header, Content, Sider } = Layout

type MenuItem = {
  key: string
  icon: React.ReactNode
  label: string
}

const menuItems: MenuItem[] = [
  { key: 'topics', icon: <SearchOutlined />, label: '选题搜索' },
  { key: 'generator', icon: <FileTextOutlined />, label: '论文生成' },
  { key: 'industry', icon: <LineChartOutlined />, label: '行业动态' },
  { key: 'competitors', icon: <FundProjectionScreenOutlined />, label: '竞品分析' },
  { key: 'settings', icon: <SettingOutlined />, label: '设置' },
]

const App: React.FC = () => {
  const [selectedMenu, setSelectedMenu] = useState('topics')
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const renderContent = () => {
    switch (selectedMenu) {
      case 'topics':
        return <TopicSearch />
      case 'generator':
        return <PaperGenerator />
      case 'industry':
        return <IndustryMonitor />
      case 'competitors':
        return <CompetitorAnalysis />
      case 'settings':
        return <div>设置页面（开发中）</div>
      default:
        return <TopicSearch />
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          🔬 科研工程助手
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedMenu]}
            onClick={({ key }) => setSelectedMenu(key)}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default App
