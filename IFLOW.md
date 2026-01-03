# iFlow CLI 项目上下文 - ygtb

## 项目概述

**ygtb** 是一个基于 Python 的多用途工具集合项目,主要包含以下功能模块:

1. **股票分析系统** - 使用 CrewAI 多智能体协作进行股票分析和投资研报生成
2. **金融分析系统** - 基于多智能体的金融交易策略分析和风险评估
3. **求职应用定制系统** - 使用 AI 智能体辅助简历定制和面试准备
4. **文章风格分析与重写工具** - 基于 Bokeh 的 Web 应用,用于分析和模仿文章写作风格
5. **网络爬虫工具集** - 用于抓取头条、书旗、掌阅等平台的内容

## 技术栈

### 核心框架
- **Python 3.13+** - 主要编程语言
- **CrewAI** - 多智能体协作框架,用于构建 AI Agent 系统
- **Bokeh** - 交互式数据可视化框架,用于构建 Web UI
- **Dash** - Web 应用框架(用于备选 UI 实现)

### 主要依赖库
- `crewai[tools]` - 多智能体框架及工具集
- `bokeh` >= 2.4.2 - 数据可视化
- `dash` >= 3.2.0 - Web 应用框架
- `selenium` >= 4.38.0 - Web 自动化测试
- `polygon-api-client` >= 1.16.3 - 股票数据 API
- `ddgs` >= 9.10.0 - DuckDuckGo 搜索工具
- `moviepy` == 1.0.3 - 视频处理
- `bs4` - HTML 解析
- `webdriver-manager` - Selenium WebDriver 管理

### LLM 提供商支持
项目支持多个 LLM 提供商,通过环境变量配置:
- **Antigravity** (默认) - 使用 `ANTIGRAVITY_API_KEY` 和 `ANTIGRAVITY_BASE_URL`
- **Dashscope (通义千问)** - 使用 `DASHSCOPE_API_KEY` 和 `DASHSCOPE_BASE_URL`
- **OpenAI** - 使用 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`
- **Ollama** - 本地部署,使用 `http://localhost:11434`
- **CustomAI** - 自定义 API,使用 `CUSTOMAI_API_KEY` 和 `CUSTOMAI_BASE_URL`

## 项目结构

```
ygtb.git/
├── main.py                    # 项目入口文件
├── utils.py                   # 通用工具函数和 LLM 配置
├── stock_analysis.py          # 股票分析研报生成工具
├── financial_analysis.py      # 金融交易策略分析系统
├── job_application.py         # 求职应用定制系统
├── article_style_analyzer.py  # 文章风格分析与重写工具 (Web 应用)
├── stock_recommadation.py     # 股票推荐系统
├── removeaudio.py             # 音频移除工具
├── pyproject.toml             # Python 项目配置
├── scrape/                    # 网络爬虫工具集目录
│   ├── web_toutiao.py         # 头条网页爬虫
│   ├── appium_toutiaoapp.py   # 头条 App 爬虫
│   ├── download_shuqi.py      # 书旗网下载工具
│   ├── download_zhangyue.py   # 掌阅下载工具
│   ├── whisper.py             # 语音转文字工具
│   └── ...
├── data/                      # 数据存储目录
│   ├── articles.json          # 文章风格数据
│   └── Stocks-data - *.csv    # 股票数据文件
└── .venv/                     # Python 虚拟环境
```

## 环境配置

### 环境变量配置文件
项目从 `~/.bbt/credentials.env` 加载环境变量,需要配置以下密钥:

```bash
# Antigravity API (默认)
ANTIGRAVITY_API_KEY=your_api_key
ANTIGRAVITY_BASE_URL=https://api.antigravity.com/v1

# Dashscope API (通义千问)
DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# OpenAI API
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Polygon API (股票数据)
POLYGON_API_KEY=your_polygon_api_key

# Serper API (搜索工具)
SERPER_API_KEY=your_serper_api_key

# Custom AI API
CUSTOMAI_API_KEY=your_api_key
CUSTOMAI_BASE_URL=your_base_url
```

### 虚拟环境
项目使用 `uv` 作为包管理工具:
```bash
# 安装依赖
uv sync

# 激活虚拟环境
.venv\Scripts\activate  # Windows
```

## 运行方式

### 1. 股票分析研报生成工具
```bash
python stock_analysis.py -t NVDA --provider antigravity
```
参数说明:
- `-t, --ticket`: 股票代码 (默认: NVDA)
- `--provider`: LLM 提供商 (dashscope/ollama/antigravity, 默认: antigravity)
- `--model`: 模型名称 (用于 ollama)

功能: 使用三个 AI 智能体(情报搜集员、分析师、投资顾问)协作生成股票投资研报

### 2. 文章风格分析与重写工具
```bash
python article_style_analyzer.py --provider antigravity --model gemini-3-flash
```
参数说明:
- `--provider`: LLM 提供商 (默认: antigravity)
- `--model`: LLM 模型名称 (可选)

功能: 启动 Bokeh Web 服务器 (端口 6006),提供图形化界面用于:
- 创建和管理写作风格
- 上传参考文章并自动生成风格描述
- 使用指定风格重写目标文章
- 查看和恢复历史记录

访问地址: `http://localhost:6006/`

### 3. 金融分析系统
```bash
python financial_analysis.py
```
功能: 使用四个 AI 智能体(数据分析师、交易策略师、交易顾问、风险管理师)进行金融交易分析和风险评估

### 4. 求职应用定制系统
```bash
python job_application.py
```
功能: 使用四个 AI 智能体(研究员、个人资料分析员、简历策略师、面试准备员)定制求职简历和准备面试材料

### 5. 网络爬虫工具
```bash
# 头条网页爬虫
python scrape/web_toutiao.py

# 头条 App 爬虫 (需要 Appium)
python scrape/appium_toutiaoapp.py

# 书旗网下载
python scrape/download_shuqi.py

# 掌阅下载
python scrape/download_zhangyue.py

# 语音转文字
python scrape/whisper.py
```

## 核心功能模块

### 1. LLM 配置管理 (utils.py)
提供统一的 LLM 初始化接口:
```python
from utils import get_llm

# 获取 LLM 实例
llm = get_llm(provider="antigravity", model="gemini-3-flash")
```

支持的提供商:
- `ollama`: 本地部署,默认模型 `codellama`
- `antigravity`: 使用 `gemini-3-flash` 模型
- `dashscope`: 使用 `qwen3-coder-plus` 模型
- `openai`: 使用 `gpt-4` 模型
- `customai`: 自定义模型

### 2. CrewAI 智能体系统
项目广泛使用 CrewAI 框架构建多智能体协作系统:

**典型智能体配置:**
```python
from crewai import Agent, Crew, Task, Process

# 创建智能体
agent = Agent(
    role="角色名称",
    goal="目标描述",
    backstory="背景故事",
    tools=[tool1, tool2],  # 可用工具
    llm=llm,
    verbose=True,
)

# 创建任务
task = Task(
    description="任务描述",
    expected_output="期望输出",
    agent=agent,
)

# 组建团队
crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential,  # 或 Process.hierarchical
)

# 执行任务
result = crew.kickoff(inputs={"input_key": "input_value"})
```

### 3. Bokeh Web 应用
`article_style_analyzer.py` 实现了一个完整的 Bokeh Web 应用:

**主要特性:**
- 交互式 Tab 界面管理多个写作风格
- 实时风格描述生成
- 文章风格重写
- 历史记录管理
- 剪贴板复制功能

**关键组件:**
- `StyleTab` 类: 单个风格标签页管理
- `make_document`: Bokeh 文档创建函数
- WebSocket 服务器: 端口 6006

## 开发规范

### 代码风格
- 使用 Python 3.13+ 特性
- 遵循 PEP 8 规范
- 使用 `ruff` 进行代码检查 (配置在 pyproject.toml)

### LLM 使用规范
- 优先使用 `utils.get_llm()` 获取 LLM 实例
- 支持多个 LLM 提供商,通过命令行参数切换
- API 密钥从环境变量加载,不硬编码

### 智能体设计规范
- 每个智能体有明确的角色、目标和背景故事
- 智能体使用 `verbose=True` 显示详细执行过程
- 任务描述使用 `expected_output` 明确期望输出

### 数据存储
- 配置数据: `data/articles.json` (文章风格)
- 历史记录: `~/.ygtb/data/history.json` (用户主目录)
- 环境变量: `~/.bbt/credentials.env` (用户主目录)

## 常见问题

### 1. LLM API 连接失败
检查环境变量配置:
```bash
# 确保 ~/.bbt/credentials.env 文件存在且包含正确的 API 密钥
cat ~/.bbt/credentials.env
```

### 2. Bokeh 服务器无法启动
检查端口占用:
```bash
# Windows
netstat -ano | findstr :6006

# 如果端口被占用,修改 article_style_analyzer.py 中的端口号
```

### 3. 虚拟环境问题
使用 `uv` 重新同步依赖:
```bash
uv sync
```

### 4. Selenium WebDriver 问题
`webdriver-manager` 会自动管理 WebDriver,确保网络连接正常

## 扩展开发

### 添加新的 LLM 提供商
在 `utils.py` 的 `get_llm_params()` 函数中添加新配置:

```python
provider_configs = {
    # ... 现有配置
    "new_provider": {
        "provider": "openai",
        "model": "model-name",
        "api_key": os.environ.get("NEW_PROVIDER_API_KEY"),
        "base_url": os.environ.get("NEW_PROVIDER_BASE_URL"),
        "error_msg": "错误信息",
    },
}
```

### 添加新的智能体系统
参考现有的 `stock_analysis.py` 或 `job_application.py`:
1. 定义智能体角色和工具
2. 创建任务链
3. 组建 Crew 并执行

### 添加新的爬虫工具
在 `scrape/` 目录下创建新脚本:
1. 使用 Selenium 或 BeautifulSoup
2. 实现数据提取和保存逻辑
3. 遵循现有脚本的风格

## 相关资源

- [CrewAI 文档](https://docs.crewai.com/)
- [Bokeh 文档](https://docs.bokeh.org/)
- [Polygon API 文档](https://polygon.io/docs/)
- [Dashscope 文档](https://help.aliyun.com/zh/dashscope/)