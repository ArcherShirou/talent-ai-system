# Talent AI System - 智能猎头系统

智能猎头系统后端服务，支持飞书多维表格集成、AI简历解析、候选人去重等功能。

## 功能特性

- 📄 **简历解析**：支持PDF、Word、图片格式，自动提取关键信息
- 🤖 **AI能力**：基于DeepSeek大模型的简历解析与候选人画像生成
- 🔍 **智能去重**：基于手机号/邮箱哈希去重
- 📊 **相似度推荐**：基于技能和工作年限的候选人相似度计算
- 📱 **飞书集成**：候选人数据同步到飞书多维表格

## 快速开始

### 1. 安装依赖

```bash
cd talent-ai-system
pip install -r requirements.txt
```

### 2. 配置百度OCR（必需）

系统使用百度OCR进行图片文字识别，每天免费1000次调用。

1. 访问 https://cloud.baidu.com/product/ocr
2. 创建应用，获取 API Key 和 Secret Key
3. 设置环境变量：

```bash
export BAIDU_OCR_API_KEY="你的API Key"
export BAIDU_OCR_SECRET_KEY="你的Secret Key"
```

### 3. 启动服务

```bash
python run_local.py
# 或
python app.py
```

服务将在 http://localhost:5000 启动。

## API 接口

### 简历解析
- `POST /api/parse-resume` - 上传简历文件进行解析
- `POST /api/parse-resume-text` - 直接提交文本进行解析

### 候选人管理
- `GET /api/candidates` - 获取候选人列表
- `GET /api/candidate/<id>` - 获取单个候选人详情
- `POST /api/save-candidate` - 保存候选人到飞书

### 候选人推荐
- `GET /api/similar/<id>` - 获取相似候选人
- `POST /api/search-candidates` - AI智能搜索

## 技术栈

- **后端**：Flask + Python
- **PDF处理**：PyMuPDF (fitz)
- **OCR识别**：百度OCR（优先）/ DeepSeek Vision（备选）
- **AI解析**：DeepSeek API
- **数据存储**：飞书多维表格

## 凭证配置

详见 [SECRET.md](SECRET.md)

## License

MIT
