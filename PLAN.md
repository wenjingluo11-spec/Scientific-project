# 科研工程桌面应用系统 - 实现方案

## 1. 项目概述

构建一个基于 Electron + React 的科研工程桌面应用，支持科研选题管理、多智能体论文生成、行业动态追踪和竞品分析。

### 核心技术栈
- **前端**: Electron + React + TypeScript + Ant Design
- **后端**: Node.js + Python (FastAPI)
- **数据库**: SQLite
- **AI**: Anthropic Claude API (多智能体系统)
- **状态管理**: Redux Toolkit
- **进程通信**: IPC (Electron)

---

## 2. 系统架构设计

### 2.1 整体架构
```
┌─────────────────────────────────────────────────────┐
│              Electron 主进程                         │
│  ├─ 窗口管理                                         │
│  ├─ IPC 通信                                         │
│  └─ 系统集成                                         │
└─────────────────────────────────────────────────────┘
                      ↕ IPC
┌─────────────────────────────────────────────────────┐
│              React 渲染进程                          │
│  ├─ UI 组件层                                        │
│  ├─ 状态管理 (Redux)                                │
│  └─ 业务逻辑层                                       │
└─────────────────────────────────────────────────────┘
                      ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────┐
│           Python FastAPI 后端服务                    │
│  ├─ 多智能体协调引擎                                 │
│  ├─ 论文生成服务                                     │
│  ├─ 数据爬取服务                                     │
│  └─ SQLite 数据访问层                                │
└─────────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────────┐
│              外部服务                                │
│  ├─ Anthropic Claude API                            │
│  ├─ 学术数据库 (arXiv, PubMed, Google Scholar)      │
│  └─ 行业资讯源                                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 多智能体架构设计

#### 角色分工型智能体系统
```
研究主管 Agent (Research Director)
    ↓ 分配任务
    ├─→ 文献调研员 Agent (Literature Researcher)
    │   └─ 负责搜索、整理相关文献和资料
    │
    ├─→ 论文撰写员 Agent (Paper Writer)
    │   └─ 负责撰写论文各个章节
    │
    ├─→ 方法论专家 Agent (Methodology Expert)
    │   └─ 负责研究方法设计和验证
    │
    ├─→ 数据分析师 Agent (Data Analyst)
    │   └─ 负责数据分析和可视化建议
    │
    └─→ 同行评审员 Agent (Peer Reviewer)
        └─ 负责评估论文质量并提出改进建议
```

**工作流程**:
1. 用户输入选题 → Research Director 分析需求
2. Literature Researcher 收集文献资料
3. Methodology Expert 设计研究方法
4. Data Analyst 提供数据分析建议
5. Paper Writer 撰写初稿
6. Peer Reviewer 评审并提出修改意见
7. 迭代优化 (最多3轮)
8. 生成最终论文

---

## 3. 目录结构设计

```
scientific-project/
├── electron/                    # Electron 主进程
│   ├── main.js                 # 主进程入口
│   ├── preload.js              # 预加载脚本
│   └── ipc-handlers.js         # IPC 处理器
│
├── src/                        # React 前端源码
│   ├── components/             # React 组件
│   │   ├── TopicSearch/        # 选题搜索模块
│   │   ├── PaperGenerator/     # 论文生成模块
│   │   ├── IndustryMonitor/    # 行业动态模块
│   │   ├── CompetitorAnalysis/ # 竞品分析模块
│   │   └── Common/             # 公共组件
│   │
│   ├── store/                  # Redux 状态管理
│   │   ├── slices/             # Redux slices
│   │   └── store.ts            # Store 配置
│   │
│   ├── services/               # API 服务层
│   │   ├── api.ts              # API 封装
│   │   └── websocket.ts        # WebSocket 连接
│   │
│   ├── types/                  # TypeScript 类型定义
│   ├── utils/                  # 工具函数
│   ├── App.tsx                 # 根组件
│   └── index.tsx               # 入口文件
│
├── backend/                    # Python FastAPI 后端
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   │
│   ├── agents/                 # 多智能体系统
│   │   ├── base_agent.py       # 智能体基类
│   │   ├── research_director.py
│   │   ├── literature_researcher.py
│   │   ├── paper_writer.py
│   │   ├── methodology_expert.py
│   │   ├── data_analyst.py
│   │   └── peer_reviewer.py
│   │
│   ├── services/               # 业务服务
│   │   ├── orchestrator.py     # 智能体协调器
│   │   ├── paper_service.py    # 论文生成服务
│   │   ├── crawler_service.py  # 数据爬取服务
│   │   └── analysis_service.py # 分析服务
│   │
│   ├── models/                 # 数据模型
│   │   ├── database.py         # 数据库连接
│   │   ├── topic.py            # 选题模型
│   │   ├── paper.py            # 论文模型
│   │   └── industry_news.py    # 行业资讯模型
│   │
│   ├── api/                    # API 路由
│   │   ├── topics.py           # 选题相关API
│   │   ├── papers.py           # 论文相关API
│   │   ├── industry.py         # 行业动态API
│   │   └── competitors.py      # 竞品分析API
│   │
│   └── utils/                  # 工具模块
│       ├── anthropic_client.py # Anthropic API 客户端
│       ├── web_scraper.py      # 网页爬虫
│       └── text_processor.py   # 文本处理
│
├── database/                   # SQLite 数据库
│   └── scientific.db           # 数据库文件
│
├── package.json                # Node.js 依赖
├── requirements.txt            # Python 依赖
├── tsconfig.json               # TypeScript 配置
└── README.md                   # 项目说明
```

---

## 4. 数据库设计

### 4.1 核心数据表

#### topics (科研选题表)
```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    field TEXT,                    -- 研究领域
    keywords TEXT,                 -- 关键词 (JSON)
    status TEXT DEFAULT 'pending', -- pending/processing/completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### papers (论文表)
```sql
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER,
    title TEXT NOT NULL,
    abstract TEXT,
    content TEXT,                  -- 完整论文内容 (Markdown)
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'draft',   -- draft/reviewing/completed
    quality_score REAL,            -- 质量评分 (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);
```

#### agent_conversations (智能体对话记录)
```sql
CREATE TABLE agent_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER,
    agent_role TEXT,               -- 智能体角色
    message TEXT,
    iteration INTEGER,             -- 迭代轮次
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);
```

#### industry_news (行业动态表)
```sql
CREATE TABLE industry_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source TEXT,
    url TEXT,
    content TEXT,
    keywords TEXT,                 -- JSON
    relevance_score REAL,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### competitors (竞品论文表)
```sql
CREATE TABLE competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER,
    title TEXT NOT NULL,
    authors TEXT,
    source TEXT,                   -- arXiv, PubMed, etc.
    url TEXT,
    abstract TEXT,
    citations INTEGER,
    published_at TIMESTAMP,
    analysis TEXT,                 -- AI 分析结果
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);
```

---

## 5. 核心功能实现方案

### 5.1 选题搜索和管理

**功能**:
- 支持按领域、关键词搜索选题方向
- 集成学术数据库 API (arXiv, Semantic Scholar)
- AI 辅助选题推荐和热度分析
- 选题收藏和分类管理

**实现要点**:
- 使用 Claude API 分析选题可行性和创新性
- 爬取 arXiv 等平台的相关论文数据
- 计算选题热度指标 (引用数、发表趋势)

### 5.2 多智能体论文生成

**工作流程**:

1. **Research Director 启动**
   - 接收用户选题
   - 分解任务并分配给各智能体
   - 协调整体进度

2. **Literature Researcher 文献调研**
   - 搜索相关文献 (通过 API 或爬虫)
   - 提取关键信息和研究方法
   - 生成文献综述初稿

3. **Methodology Expert 方法设计**
   - 根据选题设计研究方法
   - 提供实验设计建议
   - 评估方法可行性

4. **Paper Writer 论文撰写**
   - 根据文献和方法撰写各章节
   - 确保逻辑连贯性和学术规范
   - 生成初稿 (包括摘要、引言、方法、结论)

5. **Data Analyst 数据分析**
   - 提供数据可视化建议
   - 生成统计分析方案
   - 验证数据合理性

6. **Peer Reviewer 同行评审**
   - 评估论文质量 (创新性、严谨性、可读性)
   - 提出具体修改建议
   - 给出质量评分

7. **迭代优化**
   - 根据 Reviewer 意见修改
   - 最多迭代 3 轮
   - 生成最终版本

**技术实现**:
- 每个 Agent 使用独立的 Claude API 会话
- 使用 System Prompt 定义角色和任务
- 通过消息队列协调 Agent 之间的通信
- 保存完整的对话历史用于审计和优化

### 5.3 行业动态追踪

**数据源**:
- arXiv 最新论文
- Google Scholar 引用追踪
- 领域相关新闻网站
- 社交媒体学术讨论

**实现**:
- 定时爬虫任务 (每日更新)
- AI 内容摘要和关键词提取
- 相关度评分和智能推荐
- 邮件/桌面通知提醒

### 5.4 竞品分析系统

**功能**:
- 自动搜索同领域论文
- AI 对比分析优劣势
- 生成差异化建议
- 可视化竞品分布图

---

## 6. 关键技术实现

### 6.1 Anthropic API 集成

```python
# backend/utils/anthropic_client.py
import anthropic

class AnthropicClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def create_agent_message(
        self,
        role: str,
        context: str,
        task: str,
        max_tokens: int = 4000
    ):
        """创建智能体消息"""
        system_prompt = self._get_system_prompt(role)

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"{context}\n\n{task}"}
            ]
        )

        return message.content[0].text

    def _get_system_prompt(self, role: str) -> str:
        """根据角色返回系统提示词"""
        prompts = {
            "research_director": "你是一位经验丰富的科研主管...",
            "literature_researcher": "你是一位专业的文献调研专家...",
            "paper_writer": "你是一位优秀的学术论文撰写者...",
            # ... 其他角色
        }
        return prompts.get(role, "")
```

### 6.2 智能体协调器

```python
# backend/services/orchestrator.py
class AgentOrchestrator:
    def __init__(self, anthropic_client):
        self.client = anthropic_client
        self.agents = self._initialize_agents()

    async def generate_paper(self, topic: dict) -> dict:
        """协调多智能体生成论文"""
        context = {"topic": topic, "iterations": []}

        # 1. Research Director 分析
        director_analysis = await self._run_agent(
            "research_director",
            f"分析选题: {topic['title']}"
        )

        # 2. Literature Researcher 调研
        literature_review = await self._run_agent(
            "literature_researcher",
            f"调研文献: {director_analysis}"
        )

        # 3. Methodology Expert 设计方法
        methodology = await self._run_agent(
            "methodology_expert",
            f"设计研究方法: {literature_review}"
        )

        # 4-7. 后续流程...

        return final_paper
```

### 6.3 前端实时更新

使用 WebSocket 实时推送智能体工作进度:

```typescript
// src/services/websocket.ts
export class PaperGenerationSocket {
    private ws: WebSocket;

    connect(paperId: string) {
        this.ws = new WebSocket(`ws://localhost:8000/ws/paper/${paperId}`);

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // 更新进度: { agent: 'paper_writer', status: 'working', progress: 60 }
            store.dispatch(updatePaperProgress(data));
        };
    }
}
```

---

## 7. 开发步骤规划

### Phase 1: 基础架构搭建 (第1-2周)
1. 初始化 Electron + React 项目
2. 配置 TypeScript 和构建工具
3. 搭建 FastAPI 后端框架
4. 配置 SQLite 数据库和 ORM
5. 实现 IPC 通信和 API 服务

### Phase 2: 选题管理模块 (第3周)
1. 实现选题搜索界面
2. 集成学术数据库 API
3. 开发选题管理功能 (CRUD)
4. AI 选题推荐功能

### Phase 3: 多智能体系统 (第4-6周)
1. 实现 6 个智能体基类
2. 配置各角色 System Prompt
3. 开发智能体协调器
4. 实现论文生成流程
5. 添加迭代优化机制

### Phase 4: 论文生成界面 (第7周)
1. 设计论文生成向导
2. 实时进度展示
3. Markdown 编辑器集成
4. 导出功能 (PDF/Word)

### Phase 5: 行业动态和竞品分析 (第8-9周)
1. 开发爬虫服务
2. 实现动态追踪界面
3. 竞品分析功能
4. 数据可视化

### Phase 6: 测试和优化 (第10周)
1. 单元测试和集成测试
2. 性能优化
3. UI/UX 优化
4. 打包和发布

---

## 8. 技术难点和解决方案

### 8.1 多智能体协调复杂度
**挑战**: 多个 Agent 之间的消息传递和状态同步
**方案**:
- 使用消息队列 (Redis/内存队列)
- 状态机模式管理工作流
- 完整的日志记录和错误恢复

### 8.2 API 调用成本控制
**挑战**: Anthropic API 调用费用
**方案**:
- 缓存相似请求结果
- 使用更小的模型处理简单任务
- 流式输出减少重复调用
- 用户可配置迭代次数

### 8.3 学术资源爬取限制
**挑战**: 部分学术网站反爬虫
**方案**:
- 优先使用官方 API
- 合理设置爬取频率
- 使用代理和请求头轮换
- 本地缓存已获取数据

### 8.4 论文质量评估
**挑战**: 如何客观评估生成论文质量
**方案**:
- 多维度评分体系 (创新性、严谨性、可读性)
- 引入外部检查工具 (语法检查、查重)
- 人工审核和反馈循环
- 参考标准论文模板

---

## 9. 未来扩展方向

1. **云端同步**: 支持多设备数据同步
2. **团队协作**: 多用户共享选题和论文
3. **模板市场**: 不同领域的论文模板
4. **语音输入**: 语音转文字快速记录想法
5. **国际化**: 多语言支持
6. **插件系统**: 第三方工具集成

---

## 10. 预期成果

- ✅ 完整的桌面应用 (Windows/macOS/Linux)
- ✅ 支持 100+ 科研选题管理
- ✅ 6 个专业化智能体协同工作
- ✅ 自动生成高质量论文初稿
- ✅ 实时行业动态追踪
- ✅ 智能竞品分析
- ✅ 完整的数据管理和导出功能

---

**API Key**: sk-691331534d4a403fbd2add1841357a8f (已集成到配置中)
