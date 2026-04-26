#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Talent AI - 智能猎头系统
组织架构可视化 + 人才Mapping + AI简历解析 + 岗位智能匹配
"""

import os
import json
import tempfile
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# 配置 - 使用环境变量
CONFIG = {
    'deepseek': {
        'api_key': os.getenv('DEEPSEEK_API_KEY', 'sk-6d47f76977834ec99dd46d3516ad3359'),
        'base_url': 'https://api.deepseek.com/v1'
    },
    'feishu': {
        'app_id': os.getenv('FEISHU_APP_ID', 'cli_a9632f3336e31bd3'),
        'app_secret': os.getenv('FEISHU_APP_SECRET', 'tKU5Cr4e8fpQzl6QYapgHUeJp0qr5vRu'),
        'app_token': os.getenv('FEISHU_APP_TOKEN', 'ZEzYbNNuXakbNfsiBcschEYnnKd'),
        'tables': {
            'candidates': 'tblcWvC9iT3fPokE',
            'companies': 'tbl3A7QX6PLZgG5R',
            'departments': 'tblKp0IxPkzfOr6L'
        }
    }
}

# 初始化 OpenAI 客户端
openai_client = openai.OpenAI(
    api_key=CONFIG['deepseek']['api_key'],
    base_url=CONFIG['deepseek']['base_url']
)

# ==================== 基础路由 ====================

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "Talent AI", "version": "2.0"})

# ==================== 公司组织架构 API ====================

@app.route('/api/companies')
def get_companies():
    """获取公司列表及候选人统计"""
    # TODO: 从飞书多维表格读取真实数据
    return jsonify({
        "companies": [
            {"name": "美团", "candidates": 121, "logo": "美"},
            {"name": "字节跳动", "candidates": 103, "logo": "字"},
            {"name": "百度", "candidates": 82, "logo": "百"},
            {"name": "阿里巴巴", "candidates": 52, "logo": "阿"},
            {"name": "小米", "candidates": 50, "logo": "小"},
            {"name": "京东", "candidates": 48, "logo": "京"},
            {"name": "腾讯", "candidates": 47, "logo": "腾"},
            {"name": "滴滴出行", "candidates": 46, "logo": "滴"},
            {"name": "华为技术有限公司", "candidates": 40, "logo": "华"},
            {"name": "快手", "candidates": 37, "logo": "快"}
        ]
    })

@app.route('/api/company/<company_id>/org')
def get_company_org(company_id):
    """获取公司组织架构"""
    # TODO: 从飞书多维表格读取真实数据
    return jsonify({
        "name": "美团",
        "candidates": 209,
        "departments": [
            {
                "name": "运营部",
                "count": 70,
                "color": "blue",
                "sub_depts": [
                    {"name": "品牌市场组", "count": 22},
                    {"name": "用户运营组", "count": 17},
                    {"name": "增长运营组", "count": 14}
                ]
            },
            {
                "name": "技术部",
                "count": 39,
                "color": "green",
                "sub_depts": [
                    {"name": "数据工程组", "count": 22},
                    {"name": "算法AI组", "count": 6},
                    {"name": "安全组", "count": 3}
                ]
            }
        ]
    })

# ==================== AI 简历解析 ====================

@app.route('/api/resume/parse', methods=['POST'])
def parse_resume():
    """解析简历文件（PDF/图片）"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "未上传文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # 使用 PyPDF2 提取文本
        text = extract_text_from_pdf(tmp_path)
        
        # 使用 AI 提取结构化信息
        resume_data = extract_resume_info(text)
        
        # 清理临时文件
        os.unlink(tmp_path)
        
        return jsonify({
            "success": True,
            "data": resume_data
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_text_from_pdf(pdf_path):
    """从PDF提取文本"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        # 如果PyPDF2失败，尝试使用pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text
        except:
            return ""

def extract_resume_info(text):
    """使用 DeepSeek AI 提取简历结构化信息"""
    prompt = f"""分析以下简历内容，提取关键信息，返回JSON格式：

{{
    "name": "姓名",
    "email": "邮箱",
    "phone": "电话",
    "current_company": "当前公司",
    "current_position": "当前职位",
    "years_of_experience": 工作年限(数字),
    "skills": ["技能1", "技能2"],
    "education": [
        {{
            "school": "学校",
            "degree": "学位",
            "major": "专业",
            "year": "毕业年份"
        }}
    ],
    "work_experience": [
        {{
            "company": "公司",
            "position": "职位",
            "duration": "时长",
            "description": "主要职责"
        }}
    ],
    "summary": "个人简介"
}}

简历内容：
{text}

请确保返回有效的JSON格式。"""

    try:
        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        # 清理可能的markdown代码块标记
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        return json.loads(result.strip())
    except Exception as e:
        return {
            "name": "",
            "email": "",
            "phone": "",
            "error": f"AI解析失败: {str(e)}",
            "raw_text": text[:500]
        }

# ==================== AI 岗位智能匹配 ====================

@app.route('/api/jd/parse', methods=['POST'])
def parse_jd():
    """解析岗位JD，提取关键要求"""
    try:
        data = request.get_json()
        jd_text = data.get('jd', '')
        
        if not jd_text:
            return jsonify({"error": "JD内容为空"}), 400
        
        prompt = f"""分析以下岗位JD，提取关键信息，返回JSON格式：

{{
    "position": "岗位名称",
    "required_skills": ["必须技能1", "必须技能2"],
    "preferred_skills": ["加分技能"],
    "min_years": 最小年限,
    "max_years": 最大年限,
    "education": "学历要求",
    "responsibilities": ["职责1", "职责2"],
    "keywords": ["关键词1", "关键词2"]
}}

JD内容：
{jd_text}

请确保返回有效的JSON格式。"""

        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        jd_requirements = json.loads(result.strip())
        
        return jsonify({
            "success": True,
            "data": jd_requirements
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/match/calculate', methods=['POST'])
def calculate_match():
    """计算候选人与岗位的匹配度"""
    try:
        data = request.get_json()
        jd_requirements = data.get('jd_requirements', {})
        candidate_profile = data.get('candidate_profile', {})
        
        if not jd_requirements or not candidate_profile:
            return jsonify({"error": "缺少岗位要求或候选人信息"}), 400
        
        prompt = f"""你是专业的技术招聘顾问。请评估候选人与岗位的匹配度。

岗位要求：
{json.dumps(jd_requirements, ensure_ascii=False, indent=2)}

候选人画像：
{json.dumps(candidate_profile, ensure_ascii=False, indent=2)}

返回JSON格式评估报告：
{{
    "overall_score": 总分(0-100),
    "skill_match": {{
        "score": 技能匹配分(0-100),
        "matched": ["匹配的技能"],
        "missing": ["缺失的技能"],
        "partial": ["部分匹配的技能"]
    }},
    "experience_match": {{
        "score": 经验匹配分(0-100),
        "assessment": "经验评估说明"
    }},
    "recommendation": "是否推荐（推荐/可考虑/不推荐）",
    "reasons": {{
        "pros": ["优势1", "优势2"],
        "cons": ["不足1", "不足2"]
    }},
    "suggestion": "具体建议",
    "interview_questions": ["建议面试问题1", "建议面试问题2"]
}}

请确保返回有效的JSON格式。"""

        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        match_result = json.loads(result.strip())
        
        return jsonify({
            "success": True,
            "data": match_result
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/match/report', methods=['POST'])
def generate_match_report():
    """生成完整的匹配报告"""
    try:
        data = request.get_json()
        jd_text = data.get('jd', '')
        resume_text = data.get('resume', '')
        
        # 1. 解析JD
        jd_response = requests.post(
            f"http://localhost:{os.getenv('PORT', 5000)}/api/jd/parse",
            json={"jd": jd_text}
        )
        jd_requirements = jd_response.json()['data']
        
        # 2. 解析简历
        resume_data = extract_resume_info(resume_text)
        
        # 3. 计算匹配度
        match_response = requests.post(
            f"http://localhost:{os.getenv('PORT', 5000)}/api/match/calculate",
            json={
                "jd_requirements": jd_requirements,
                "candidate_profile": resume_data
            }
        )
        match_result = match_response.json()['data']
        
        # 4. 生成完整报告
        report = {
            "candidate": resume_data,
            "jd_requirements": jd_requirements,
            "match_result": match_result,
            "generated_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "data": report
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== 飞书多维表格操作 ====================

def get_feishu_token():
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {
        "app_id": CONFIG['feishu']['app_id'],
        "app_secret": CONFIG['feishu']['app_secret']
    }
    response = requests.post(url, json=data)
    return response.json()['tenant_access_token']

@app.route('/api/feishu/candidate/add', methods=['POST'])
def add_candidate_to_feishu():
    """将候选人添加到飞书多维表格"""
    try:
        data = request.get_json()
        candidate = data.get('candidate', {})
        
        token = get_feishu_token()
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{CONFIG['feishu']['app_token']}/tables/{CONFIG['feishu']['tables']['candidates']}/records"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 构建记录字段
        fields = {
            "姓名": candidate.get('name', ''),
            "邮箱": candidate.get('email', ''),
            "电话": candidate.get('phone', ''),
            "技能标签": candidate.get('skills', []),
            "当前公司": candidate.get('current_company', ''),
            "当前职位": candidate.get('current_position', ''),
            "工作年限": candidate.get('years_of_experience', 0),
            "跟进状态": "待联系",
            "创建时间": int(datetime.now().timestamp() * 1000)
        }
        
        payload = {
            "fields": fields
        }
        
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        if result.get('code') == 0:
            return jsonify({
                "success": True,
                "record_id": result['data']['record']['record_id']
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('msg', '未知错误')
            }), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/feishu/candidate/search', methods=['POST'])
def search_candidate_in_feishu():
    """在飞书多维表格中搜索候选人"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        
        token = get_feishu_token()
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{CONFIG['feishu']['app_token']}/tables/{CONFIG['feishu']['tables']['candidates']}/records/search"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "view_id": "",
            "field_names": ["姓名", "当前公司", "技能标签"],
            "sort": [],
            "filter": {
                "conjunction": "or",
                "conditions": [
                    {
                        "field_name": "姓名",
                        "operator": "contains",
                        "value": [keyword]
                    }
                ]
            } if keyword else {},
            "automatic_fields": False
        }
        
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        if result.get('code') == 0:
            candidates = []
            for item in result['data']['items']:
                fields = item['fields']
                candidates.append({
                    "record_id": item['record_id'],
                    "name": fields.get('姓名', ''),
                    "email": fields.get('邮箱', ''),
                    "company": fields.get('当前公司', ''),
                    "skills": fields.get('技能标签', [])
                })
            
            return jsonify({
                "success": True,
                "candidates": candidates,
                "total": len(candidates)
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('msg', '未知错误')
            }), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== GitHub 人才搜索 ====================

@app.route('/api/github/search', methods=['POST'])
def search_github_developers():
    """搜索 GitHub 开发者"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        language = data.get('language', '')
        location = data.get('location', '')
        
        # 构建搜索关键词
        search_terms = []
        if query:
            search_terms.append(query)
        if language:
            search_terms.append(f"language:{language}")
        if location:
            search_terms.append(f"location:{location}")
        
        search_query = " ".join(search_terms)
        
        # 使用 GitHub API 搜索用户
        url = f"https://api.github.com/search/users?q={search_query}&sort=followers&order=desc&per_page=10"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Talent-AI-System"
        }
        
        response = requests.get(url, headers=headers)
        result = response.json()
        
        developers = []
        for user in result.get('items', []):
            # 获取用户详细信息
            user_url = user['url']
            user_response = requests.get(user_url, headers=headers)
            user_data = user_response.json()
            
            developers.append({
                "username": user_data.get('login', ''),
                "name": user_data.get('name', ''),
                "avatar": user_data.get('avatar_url', ''),
                "bio": user_data.get('bio', ''),
                "location": user_data.get('location', ''),
                "company": user_data.get('company', ''),
                "blog": user_data.get('blog', ''),
                "followers": user_data.get('followers', 0),
                "public_repos": user_data.get('public_repos', 0),
                "profile_url": user_data.get('html_url', '')
            })
        
        return jsonify({
            "success": True,
            "developers": developers,
            "total": result.get('total_count', 0)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== 主程序 ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Talent AI 运行在 http://localhost:{port}")
    print(f"📋 API 文档: http://localhost:{port}/health")
    app.run(host='0.0.0.0', port=port, debug=False)