# Talent AI System - AI智能猎头系统

完整的 AI 驱动猎头系统，支持组织架构可视化、人才 Mapping、简历智能解析、岗位匹配、飞书集成。

## ✨ 核心功能

### 🎯 组织架构可视化
- 公司列表 + 候选人统计
- 部门层级展示（一级部门 → 二级部门 → 岗位）
- 人才 Mapping 统计

### 🤖 AI 智能匹配（核心亮点）
解决猎头痛点：不了解岗位需求，不知道候选人是否合适

**功能流程**：
1. **JD 解析**：自动提取技术栈、年限要求、职责
2. **候选人画像**：从简历提取真实技能、项目经验
3. **匹配评分**：计算技术匹配度、经验匹配度、综合评分
4. **报告生成**：输出匹配理由（为什么合适/为什么不合适）

**示例场景**：
- ❌ 错误推送：把大模型加速推理岗位推给了算法工程师
- ✅ 智能匹配：AI 分析 JD 要求 CUDA/TensorRT，候选人简历有 GPU 优化经验，评分 85 分

### 📄 简历智能解析
- 支持 PDF/Word/图片格式
- DeepSeek AI 解析结构化信息
- 自动提取：姓名、邮箱、电话、技能、工作经历
- 实时关联飞书多维表格

### 🔍 GitHub 人才搜索
- 搜索 GitHub 开发者
- 提取仓库和技能信息
- 筛选优质候选人

### 📊 飞书多维表格集成
- 候选人数据自动入库
- 公司/部门自动关联
- 实时 Mapping 更新

## 🚀 快速开始

### 方式一：本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/ArcherShirou/talent-ai-system.git
cd talent-ai-system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
export DEEPSEEK_API_KEY="sk-xxxxx"
export FEISHU_APP_ID="cli_xxxxx"
export FEISHU_APP_SECRET="xxxxx"
export FEISHU_APP_TOKEN="xxxxx"

# 4. 启动服务
python app.py
```

访问：http://localhost:5000

### 方式二：云端部署（Render）

#### 步骤 1：Fork 仓库
点击右上角 Fork 按钮

#### 步骤 2：在 Render 创建服务
1. 访问 https://render.com
2. 点击 "New +" → "Blueprint"
3. 连接你的 GitHub 仓库
4. Render 会自动识别 `render.yaml` 配置

#### 步骤 3：配置环境变量
在 Render 控制台添加以下环境变量：
- `DEEPSEEK_API_KEY`: DeepSeek API 密钥
- `FEISHU_APP_ID`: 飞书应用 ID
- `FEISHU_APP_SECRET`: 飞书应用密钥
- `FEISHU_APP_TOKEN`: 飞书多维表格 Token

#### 步骤 4：部署完成
Render 会自动构建和部署，完成后获得公网访问地址

## 📋 API 接口

### 基础接口
- `GET /` - 前端页面
- `GET /health` - 健康检查

### 组织架构
- `GET /api/companies` - 获取公司列表
- `GET /api/company/<company_id>/org` - 获取公司组织架构

### 简历解析
- `POST /api/resume/parse` - 上传简历文件解析
  ```json
  {
    "file": "<PDF文件>"
  }
  ```

### AI 岗位匹配
- `POST /api/jd/parse` - 解析岗位 JD
  ```json
  {
    "jd": "岗位JD文本内容"
  }
  ```

- `POST /api/match/calculate` - 计算匹配度
  ```json
  {
    "jd_requirements": {...},
    "candidate_profile": {...}
  }
  ```

- `POST /api/match/report` - 生成完整匹配报告
  ```json
  {
    "jd": "岗位JD文本",
    "resume": "简历文本"
  }
  ```

### 飞书集成
- `POST /api/feishu/candidate/add` - 添加候选人到飞书表格
- `POST /api/feishu/candidate/search` - 搜索飞书表格中的候选人

### GitHub 搜索
- `POST /api/github/search` - 搜索 GitHub 开发者
  ```json
  {
    "query": "AI engineer",
    "language": "Python",
    "location": "China"
  }
  ```

## 🎨 前端设计

参考 Claude Code 风格，简洁现代的深色主题：
- 左侧导航：公司列表
- 右侧内容：组织架构可视化 + 人才 Mapping

## 🔧 技术栈

- **前端**: Vue 3 + 原生 CSS
- **后端**: Python Flask
- **AI**: DeepSeek API
- **数据**: 飞书多维表格
- **部署**: Render / Railway / Heroku

## 📦 项目结构

```
talent-ai-system/
├── app.py              # 后端 API
├── index.html          # 前端页面
├── requirements.txt    # Python 依赖
├── render.yaml         # Render 部署配置
├── Procfile            # Heroku 部署配置
└── README.md           # 项目说明
```

## 🔐 环境变量

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | https://platform.deepseek.com |
| FEISHU_APP_ID | 飞书应用 ID | 飞书开放平台 |
| FEISHU_APP_SECRET | 飞书应用密钥 | 飞书开放平台 |
| FEISHU_APP_TOKEN | 飞书多维表格 Token | 多维表格 URL |

## 🎯 使用示例

### 示例 1：简历解析 + AI 匹配

```python
import requests

# 1. 上传简历
with open('resume.pdf', 'rb') as f:
    response = requests.post(
        'http://your-domain/api/resume/parse',
        files={'file': f}
    )
candidate = response.json()['data']

# 2. 解析 JD
jd_text = """
大模型加速推理工程师
- 3年以上 CUDA/GPU 编程经验
- 熟悉 TensorRT、Triton 推理框架
"""
response = requests.post(
    'http://your-domain/api/jd/parse',
    json={'jd': jd_text}
)
jd_requirements = response.json()['data']

# 3. 计算匹配度
response = requests.post(
    'http://your-domain/api/match/calculate',
    json={
        'jd_requirements': jd_requirements,
        'candidate_profile': candidate
    }
)
match_result = response.json()['data']

print(f"匹配分数: {match_result['overall_score']}/100")
print(f"推荐建议: {match_result['recommendation']}")
```

### 示例 2：GitHub 人才搜索

```python
import requests

response = requests.post(
    'http://your-domain/api/github/search',
    json={
        'query': 'PyTorch LLM',
        'language': 'Python',
        'location': 'China'
    }
)

developers = response.json()['developers']
for dev in developers:
    print(f"{dev['name']} - {dev['company']} - {dev['followers']} followers")
```

## 📝 开发计划

- [ ] 前端与后端联调
- [ ] 实时 Mapping 功能完善
- [ ] 批量简历上传
- [ ] 邮件自动触达
- [ ] 候选人管理界面

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License