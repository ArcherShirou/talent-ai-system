#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Talent AI - 智能猎头系统后端服务
支持飞书多维表格集成、AI简历解析、候选人去重、相似度推荐等功能
"""

import os
import json
import re
import hashlib
import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# AI Resume Parsing
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 飞书 API
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# PDF Parsing
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ============ 配置 ============
CONFIG = {
    'feishu': {
        'app_id': os.getenv('FEISHU_APP_ID', 'cli_a9632f3336e31bd3'),
        'app_secret': os.getenv('FEISHU_APP_SECRET', 'tKU5Cr4e8fpQzl6QYapgHUeJp0qr5vRu'),
        'app_token': os.getenv('FEISHU_APP_TOKEN', 'X8mFbCyJla7G1uspstRctdeUnog'),
        'table_id': os.getenv('FEISHU_TABLE_ID', 'tblKoDiAbTQ8Cd13'),
        'fields': {
            'name': '姓名',
            'phone': '手机',
            'email': '邮箱',
            'company': '公司名称',
            'position': '职位',
            'resume': '简历原文',
            'years': '工作年限',
            'education': '学历',
            'skills': '技能标签',
            'profile': '候选人画像',
            'score': '能力评分',
            'source': '来源'
        }
    },
    'deepseek': {
        'api_key': os.getenv('DEEPSEEK_API_KEY', 'sk-6d47f76977834ec99dd46d3516ad3359'),
        'base_url': 'https://api.deepseek.com/v1'
    }
}

# 内存数据库（演示用）
DB = {
    'candidates': [
        {
            'id': '1',
            'name': '张三',
            'phone': '13812345678',
            'email': 'zhangsan@email.com',
            'company': '字节跳动',
            'position': '高级前端工程师',
            'status': 'ACTIVE',
            'score': 92,
            'skills': 'Vue, React, TypeScript',
            'years': 5,
            'education': '本科',
            'source': '猎聘网',
            'profile': '10年+互联网经验，曾主导多个大型项目的前端架构设计。擅长性能优化和团队管理。',
            'resume': '',
            'created_at': '2024-01-15'
        },
        {
            'id': '2',
            'name': '李四',
            'phone': '13987654321',
            'email': 'lisi@email.com',
            'company': '美团',
            'position': '后端架构师',
            'status': 'INTERVIEW',
            'score': 88,
            'skills': 'Java, Python, 分布式系统',
            'years': 8,
            'education': '硕士',
            'source': 'Boss直聘',
            'profile': '分布式系统专家，曾在阿里云工作5年。',
            'resume': '',
            'created_at': '2024-01-16'
        },
        {
            'id': '3',
            'name': '王五',
            'phone': '13712345987',
            'email': 'wangwu@email.com',
            'company': '百度',
            'position': '产品经理',
            'status': 'PENDING',
            'score': 85,
            'skills': '产品设计, 数据分析, 用户研究',
            'years': 6,
            'education': '本科',
            'source': '内部推荐',
            'profile': '资深产品经理，擅长C端产品设计。',
            'resume': '',
            'created_at': '2024-01-17'
        },
        {
            'id': '4',
            'name': '赵六',
            'phone': '13698765432',
            'email': 'zhaoliu@email.com',
            'company': '腾讯',
            'position': 'UI设计师',
            'status': 'ACTIVE',
            'score': 90,
            'skills': 'Figma, Sketch, 交互设计',
            'years': 4,
            'education': '本科',
            'source': '站酷',
            'profile': '知名互联网公司设计经验，作品多次获奖。',
            'resume': '',
            'created_at': '2024-01-18'
        },
        {
            'id': '5',
            'name': '钱七',
            'phone': '13567891234',
            'email': 'qianqi@email.com',
            'company': '阿里巴巴',
            'position': '算法工程师',
            'status': 'INTERVIEW',
            'score': 95,
            'skills': 'Python, TensorFlow, 深度学习',
            'years': 7,
            'education': '博士',
            'source': '猎头寻访',
            'profile': 'AI领域专家，发表多篇顶会论文。',
            'resume': '',
            'created_at': '2024-01-19'
        }
    ],
    'interviews': [
        {
            'id': '1',
            'candidate_id': '1',
            'candidate_name': '张三',
            'position': '高级前端工程师',
            'round': '第二轮',
            'interviewer': '李经理',
            'date': '2024-03-15 14:00',
            'status': '通过',
            'notes': ''
        },
        {
            'id': '2',
            'candidate_id': '2',
            'candidate_name': '李四',
            'position': '后端架构师',
            'round': '第一轮',
            'interviewer': '王总监',
            'date': '2024-03-16 10:00',
            'status': '待评价',
            'notes': ''
        }
    ],
    'reminders': [
        {
            'id': '1',
            'candidate_id': '1',
            'title': '张三面试反馈',
            'type': 'interview',
            'time': '2024-03-15 16:00',
            'status': 'pending',
            'created_at': '2024-03-14'
        },
        {
            'id': '2',
            'candidate_id': '2',
            'title': '李四简历跟进',
            'type': 'followup',
            'time': '2024-03-16 10:00',
            'status': 'pending',
            'created_at': '2024-03-14'
        }
    ],
    'companies': [
        {'id': '1', 'name': '美团', 'color': '#FF6B00', 'candidate_count': 45, 'level1_depts': 5, 'dept_count': 12},
        {'id': '2', 'name': '字节跳动', 'color': '#0057FF', 'candidate_count': 68, 'level1_depts': 6, 'dept_count': 15},
        {'id': '3', 'name': '百度', 'color': '#2932E1', 'candidate_count': 32, 'level1_depts': 4, 'dept_count': 9},
        {'id': '4', 'name': '阿里巴巴', 'color': '#FF5000', 'candidate_count': 52, 'level1_depts': 5, 'dept_count': 11},
        {'id': '5', 'name': '腾讯', 'color': '#07C160', 'candidate_count': 41, 'level1_depts': 4, 'dept_count': 10},
        {'id': '6', 'name': '小米', 'color': '#FF6900', 'candidate_count': 28, 'level1_depts': 3, 'dept_count': 8},
        {'id': '7', 'name': '华为', 'color': '#D40000', 'candidate_count': 55, 'level1_depts': 6, 'dept_count': 14},
        {'id': '8', 'name': '京东', 'color': '#E1251B', 'candidate_count': 35, 'level1_depts': 4, 'dept_count': 9}
    ]
}

# ============ 工具函数 ============

def generate_id():
    """生成唯一ID"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:4]
    return f"{timestamp}-{random_str}"

def hash_phone(phone):
    """哈希手机号用于去重"""
    if not phone:
        return None
    clean_phone = re.sub(r'\D', '', phone)
    return hashlib.md5(clean_phone.encode()).hexdigest()

def hash_email(email):
    """哈希邮箱用于去重"""
    if not email:
        return None
    return hashlib.md5(email.lower().strip().encode()).hexdigest()

def calculate_similarity(candidate1, candidate2):
    """计算两个候选人的相似度"""
    skills1 = set(s.strip().lower() for s in candidate1.get('skills', '').split(','))
    skills2 = set(s.strip().lower() for s in candidate2.get('skills', '').split(','))
    
    if not skills1 or not skills2:
        return 0
    
    intersection = skills1 & skills2
    union = skills1 | skills2
    
    jaccard = len(intersection) / len(union) if union else 0
    
    # 考虑工作年限相似度
    years1 = candidate1.get('years', 0)
    years2 = candidate2.get('years', 0)
    years_diff = abs(years1 - years2) / 10
    years_sim = max(0, 1 - years_diff)
    
    # 综合相似度
    return int((jaccard * 0.7 + years_sim * 0.3) * 100)

def calculate_score(candidate_data):
    """AI能力评分 (0-100)"""
    score = 50  # 基础分
    
    # 工作年限加分
    years = candidate_data.get('years', 0)
    score += min(years * 2, 20)
    
    # 学历加分
    edu = candidate_data.get('education', '')
    edu_scores = {'博士': 15, '硕士': 12, '本科': 8, '大专': 5}
    score += edu_scores.get(edu, 0)
    
    # 技能数量加分
    skills = candidate_data.get('skills', '')
    skill_count = len([s for s in skills.split(',') if s.strip()])
    score += min(skill_count * 3, 15)
    
    return min(score, 100)

def generate_profile(candidate_data):
    """生成候选人画像"""
    name = candidate_data.get('name', '')
    years = candidate_data.get('years', 0)
    position = candidate_data.get('position', '')
    company = candidate_data.get('company', '')
    skills = candidate_data.get('skills', '')
    education = candidate_data.get('education', '')
    
    profile = f"{name}，{education}学历，拥有{years}年工作经验。 "
    profile += f"擅长{skills}。 "
    if company:
        profile += f"目前/曾就职于{company}担任{position}。"
    
    return profile

# ============ 飞书 API ============

def get_feishu_token():
    """获取飞书访问令牌（tenant_access_token）"""
    app_id = os.getenv('FEISHU_APP_ID', CONFIG['feishu'].get('app_id', 'cli_a9632f3336e31bd3'))
    app_secret = os.getenv('FEISHU_APP_SECRET', CONFIG['feishu'].get('app_secret', 'tKU5Cr4e8fpQzl6QYapgHUeJp0qr5vRu'))
    
    if not app_secret:
        # 尝试从配置中获取
        app_secret = CONFIG['feishu'].get('app_secret', '')
    
    if not app_id or not app_secret:
        print('警告: 缺少飞书App ID或App Secret，无法获取访问令牌')
        return ''
    
    try:
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        response = requests.post(url, json={
            'app_id': app_id,
            'app_secret': app_secret
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return data.get('tenant_access_token', '')
            else:
                print(f'获取飞书token失败: {data}')
        return ''
    except Exception as e:
        print(f'获取飞书token异常: {e}')
        return ''

def fetch_candidates_from_feishu():
    """从飞书多维表格获取候选人数据"""
    if not REQUESTS_AVAILABLE:
        return None
    
    try:
        token = get_feishu_token()
        if not token:
            return None
        
        base_url = 'https://open.feishu.cn/open-apis/bitable/v1'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 获取记录
        url = f"{base_url}/apps/{CONFIG['feishu']['app_token']}/tables/{CONFIG['feishu']['table_id']}/records"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('data', {}).get('items', [])
            
            candidates = []
            for record in records:
                fields = record.get('fields', {})
                candidates.append({
                    'id': record.get('record_id', ''),
                    'name': fields.get(CONFIG['feishu']['fields']['name'], ''),
                    'phone': fields.get(CONFIG['feishu']['fields']['phone'], ''),
                    'email': fields.get(CONFIG['feishu']['fields']['email'], ''),
                    'company': fields.get(CONFIG['feishu']['fields']['company'], ''),
                    'position': fields.get(CONFIG['feishu']['fields']['position'], ''),
                    'years': fields.get(CONFIG['feishu']['fields']['years'], 0),
                    'education': fields.get(CONFIG['feishu']['fields']['education'], ''),
                    'skills': fields.get(CONFIG['feishu']['fields']['skills'], ''),
                    'profile': fields.get(CONFIG['feishu']['fields']['profile'], ''),
                    'score': fields.get(CONFIG['feishu']['fields']['score'], 0),
                    'source': fields.get(CONFIG['feishu']['fields']['source'], '')
                })
            
            return candidates
    except Exception as e:
        print(f"Error fetching from Feishu: {e}")
    
    return None

def save_candidate_to_feishu(candidate_data):
    """保存候选人到飞书多维表格"""
    if not REQUESTS_AVAILABLE:
        return False, None
    
    try:
        token = get_feishu_token()
        if not token:
            return False, 'No access token'
        
        base_url = 'https://open.feishu.cn/open-apis/bitable/v1'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 准备字段数据
        fields = {
            CONFIG['feishu']['fields']['name']: candidate_data.get('name', ''),
            CONFIG['feishu']['fields']['phone']: candidate_data.get('phone', ''),
            CONFIG['feishu']['fields']['email']: candidate_data.get('email', ''),
            CONFIG['feishu']['fields']['company']: candidate_data.get('company', ''),
            CONFIG['feishu']['fields']['position']: candidate_data.get('position', ''),
            CONFIG['feishu']['fields']['years']: candidate_data.get('years', 0),
            CONFIG['feishu']['fields']['education']: candidate_data.get('education', ''),
            CONFIG['feishu']['fields']['skills']: candidate_data.get('skills', ''),
            CONFIG['feishu']['fields']['profile']: candidate_data.get('profile', ''),
            CONFIG['feishu']['fields']['score']: candidate_data.get('score', 0),
            CONFIG['feishu']['fields']['source']: candidate_data.get('source', '')
        }
        
        url = f"{base_url}/apps/{CONFIG['feishu']['app_token']}/tables/{CONFIG['feishu']['table_id']}/records"
        response = requests.post(url, headers=headers, json={'fields': fields}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            record_id = data.get('data', {}).get('record', {}).get('record_id')
            return True, record_id
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)



def extract_text_from_pdf(file_content):
    """从PDF文件中提取文本"""
    if not PDF_AVAILABLE:
        return None, "PyMuPDF not available"
    
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text, None
    except Exception as e:
        return None, str(e)

# ============ AI 简历解析 ============

def parse_resume_with_ai(resume_text):
    """使用 AI 解析简历"""
    if not OPENAI_AVAILABLE:
        return parse_resume_rule_based(resume_text)
    
    try:
        client = openai.OpenAI(
            api_key=CONFIG['deepseek']['api_key'],
            base_url=CONFIG['deepseek']['base_url']
        )
        
        prompt = """请从以下简历文本中提取关键信息，以JSON格式返回：
{
    "name": "姓名",
    "phone": "手机号",
    "email": "邮箱",
    "years": 工作年限数字,
    "education": "学历",
    "skills": ["技能1", "技能2"],
    "experience": [{"company": "公司", "position": "职位", "duration": "时间"}],
    "summary": "个人总结"
}

简历内容：
""" + resume_text
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的简历解析助手。请从简历中提取结构化信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content
        
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            return json.loads(json_match.group())
        
        return parse_resume_rule_based(resume_text)
        
    except Exception as e:
        print(f"AI parsing error: {e}")
        return parse_resume_rule_based(resume_text)

def parse_resume_rule_based(text):
    """基于规则的简历解析"""
    result = {
        'name': '',
        'phone': '',
        'email': '',
        'years': 0,
        'education': '',
        'skills': [],
        'experience': [],
        'summary': ''
    }
    
    # 提取姓名（通常是第一行或"姓名："后）
    name_match = re.search(r'姓名[：:]\s*([^\n]+)', text)
    if name_match:
        result['name'] = name_match.group(1).strip()
    
    # 提取手机号
    phone_match = re.search(r'(1[3-9]\d{9})', text)
    if phone_match:
        result['phone'] = phone_match.group(1)
    
    # 提取邮箱
    email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
    if email_match:
        result['email'] = email_match.group()
    
    # 提取工作年限
    years_match = re.search(r'(\d+)\s*年', text)
    if years_match:
        result['years'] = int(years_match.group(1))
    
    # 提取学历
    edu_levels = ['博士', '硕士', '本科', '大专', '高中', '中专']
    for edu in edu_levels:
        if edu in text:
            result['education'] = edu
            break
    
    # 提取技能
    skill_keywords = ['Python', 'Java', 'JavaScript', 'Vue', 'React', 'Node', 'Go', 'Rust',
                      'MySQL', 'Redis', 'MongoDB', 'Kafka', 'Docker', 'K8s', 'AWS', 'Azure',
                      'Git', 'Linux', 'TensorFlow', 'PyTorch', 'NLP', 'CV', 'AI', 'ML',
                      '前端', '后端', '全栈', '移动端', 'iOS', 'Android', 'Flutter',
                      '产品', '运营', '设计', '测试', '运维', '架构', '算法']
    
    found_skills = []
    for skill in skill_keywords:
        if skill in text:
            found_skills.append(skill)
    
    result['skills'] = found_skills[:10]  # 最多10个
    
    return result

def generate_ai_profile(candidate_data):
    """使用 AI 生成候选人画像"""
    if not OPENAI_AVAILABLE:
        return generate_profile(candidate_data)
    
    try:
        client = openai.OpenAI(
            api_key=CONFIG['deepseek']['api_key'],
            base_url=CONFIG['deepseek']['base_url']
        )
        
        prompt = f"""根据以下候选人信息，生成一段专业的人才画像总结（100字以内）：

姓名：{candidate_data.get('name', '')}
工作年限：{candidate_data.get('years', 0)}年
学历：{candidate_data.get('education', '')}
职位：{candidate_data.get('position', '')}
公司：{candidate_data.get('company', '')}
技能：{candidate_data.get('skills', '')}

请从专业能力、职业发展、优势特点等方面进行总结。"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的人才分析师，擅长生成精准的人才画像描述。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"AI profile generation error: {e}")
        return generate_profile(candidate_data)

# ============ AI 初级搜寻员功能 ============

def ai_smart_search(job_requirement):
    """AI智能搜索 - 分析岗位需求并搜索候选人"""
    if not OPENAI_AVAILABLE:
        return smart_search_rule_based(job_requirement)
    
    try:
        client = openai.OpenAI(
            api_key=CONFIG['deepseek']['api_key'],
            base_url=CONFIG['deepseek']['base_url']
        )
        
        prompt = f"""分析以下岗位需求，提取关键搜索条件：

岗位需求：{job_requirement}

请以JSON格式返回：
{{
    "keywords": ["关键词1", "关键词2", ...],  // 提取的技能/职位关键词
    "experience_range": "{{min}}-{{max}}",  // 工作经验范围
    "industry": "行业背景",  // 要求的行业背景
    "education": "学历要求",  // 学历要求
    "search_conditions": {{  // 搜索条件详情
        "required_skills": [...],
        "preferred_industry": [...],
        "years_required": {{"min": 0, "max": 10}}
    }}
}}

只返回JSON，不要有其他内容。"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的猎头顾问，擅长分析岗位需求。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            return json.loads(json_match.group())
        
        return smart_search_rule_based(job_requirement)
        
    except Exception as e:
        print(f"AI smart search error: {e}")
        return smart_search_rule_based(job_requirement)

def smart_search_rule_based(requirement):
    """基于规则的智能搜索"""
    requirement_lower = requirement.lower()
    
    keywords = []
    if 'java' in requirement_lower:
        keywords.extend(['Java', 'Spring', 'JVM'])
    if '前端' in requirement_lower or 'front' in requirement_lower:
        keywords.extend(['Vue', 'React', 'JavaScript', '前端'])
    if '后端' in requirement_lower or 'back' in requirement_lower:
        keywords.extend(['后端', 'Python', 'Go', 'Java'])
    if '算法' in requirement_lower:
        keywords.extend(['算法', '机器学习', '深度学习', 'Python'])
    if '产品' in requirement_lower:
        keywords.extend(['产品经理', '产品设计'])
    if '运营' in requirement_lower:
        keywords.extend(['运营', '用户增长'])
    
    years_min, years_max = 0, 20
    years_match = re.search(r'(\d+)[-~](\d+)\s*年', requirement)
    if years_match:
        years_min, years_max = int(years_match.group(1)), int(years_match.group(2))
    else:
        years_match = re.search(r'(\d+)\s*年以上', requirement)
        if years_match:
            years_min = int(years_match.group(1))
    
    industries = []
    if '电商' in requirement_lower:
        industries.append('电商')
    if '金融' in requirement_lower:
        industries.append('金融')
    if '互联网' in requirement_lower:
        industries.append('互联网')
    
    return {
        "keywords": keywords if keywords else [requirement],
        "experience_range": f"{years_min}-{years_max}",
        "industry": industries[0] if industries else "不限",
        "education": "本科" if "本科" in requirement else ("硕士" if "硕士" in requirement else "不限"),
        "search_conditions": {
            "required_skills": keywords,
            "preferred_industry": industries,
            "years_required": {"min": years_min, "max": years_max}
        }
    }

def calculate_match_score(candidate, search_conditions):
    """计算候选人与岗位的匹配度"""
    score = 0
    matched_skills = []
    missing_skills = []
    reasons = []
    
    required_skills = search_conditions.get('required_skills', [])
    candidate_skills = set(s.strip().lower() for s in candidate.get('skills', '').split(','))
    
    # 技能匹配
    if required_skills:
        matched = []
        for skill in required_skills:
            skill_lower = skill.lower()
            if any(skill_lower in cs for cs in candidate_skills):
                matched.append(skill)
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
        
        skill_score = len(matched) / len(required_skills) * 50 if required_skills else 25
        score += skill_score
        
        if matched:
            reasons.append(f"技能匹配：{'、'.join(matched[:3])}")
    
    # 工作经验匹配
    years_required = search_conditions.get('years_required', {})
    years_min = years_required.get('min', 0)
    years_max = years_required.get('max', 20)
    candidate_years = candidate.get('years', 0)
    
    if years_min <= candidate_years <= years_max:
        score += 25
        reasons.append(f"工作年限符合要求（{candidate_years}年）")
    elif candidate_years < years_min:
        score += max(0, 15 - (years_min - candidate_years) * 3)
        reasons.append(f"工作年限偏少（{candidate_years}年，要求{years_min}+年）")
    else:
        score += max(0, 20 - (candidate_years - years_max) * 2)
        reasons.append(f"工作年限偏高（{candidate_years}年）")
    
    # 行业背景匹配
    preferred_industry = search_conditions.get('preferred_industry', [])
    if preferred_industry and any(ind in candidate.get('company', '') for ind in preferred_industry):
        score += 15
        reasons.append("有相关行业背景")
    elif preferred_industry:
        score += 5
        reasons.append("无特定行业背景要求")
    
    # 学历匹配
    edu_required = search_conditions.get('education', '不限')
    candidate_edu = candidate.get('education', '')
    if edu_required == '不限' or candidate_edu:
        score += 10
    if candidate_edu == '硕士' or candidate_edu == '博士':
        reasons.append(f"学历优秀：{candidate_edu}")
    
    return {
        'total_score': min(int(score), 100),
        'skill_score': min(int(skill_score), 50),
        'experience_score': min(int(25 if years_min <= candidate_years <= years_max else 15), 25),
        'industry_score': min(int(15 if preferred_industry and any(ind in candidate.get('company', '') for ind in preferred_industry) else 5), 15),
        'education_score': min(int(10 if candidate_edu else 5), 10),
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'match_reasons': reasons
    }

def ai_evaluate_candidate(candidate_data, job_requirement):
    """AI评估候选人适合度"""
    if not OPENAI_AVAILABLE:
        return evaluate_candidate_rule_based(candidate_data, job_requirement)
    
    try:
        client = openai.OpenAI(
            api_key=CONFIG['deepseek']['api_key'],
            base_url=CONFIG['deepseek']['base_url']
        )
        
        prompt = f"""作为专业猎头顾问，请评估以下候选人与岗位的匹配度：

【候选人信息】
姓名：{candidate_data.get('name', '未知')}
工作年限：{candidate_data.get('years', 0)}年
学历：{candidate_data.get('education', '未知')}
当前职位：{candidate_data.get('position', '未知')}
当前公司：{candidate_data.get('company', '未知')}
技能：{candidate_data.get('skills', '未知')}
画像：{candidate_data.get('profile', '暂无')}

【岗位需求】
{job_requirement}

请以JSON格式返回详细评估报告：
{{
    "overall_score": 85,  // 综合评分 0-100
    "skill_match_score": 90,  // 技能匹配度 0-100
    "experience_match_score": 85,  // 经验匹配度 0-100
    "growth_potential": "高/中/低",  // 成长潜力
    "risk_points": ["风险点1", "风险点2"],  // 潜在风险
    "strengths": ["优势1", "优势2"],  // 核心优势
    "weaknesses": ["劣势1", "劣势2"],  // 潜在劣势
    "recommendation": "推荐理由",
    "suitable_scenarios": ["适合场景1", "适合场景2"]  // 适合的场景
}}

只返回JSON。"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的猎头顾问，擅长候选人评估。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=800
        )
        
        result = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            return json.loads(json_match.group())
        
        return evaluate_candidate_rule_based(candidate_data, job_requirement)
        
    except Exception as e:
        print(f"AI evaluation error: {e}")
        return evaluate_candidate_rule_based(candidate_data, job_requirement)

def evaluate_candidate_rule_based(candidate_data, job_requirement):
    """基于规则的候选人评估"""
    score = 70
    
    strengths = []
    weaknesses = []
    risk_points = []
    
    years = candidate_data.get('years', 0)
    if years >= 5:
        score += 10
        strengths.append("经验丰富，工作年限较长")
    elif years < 2:
        score -= 10
        weaknesses.append("工作年限较短")
    
    edu = candidate_data.get('education', '')
    if edu in ['硕士', '博士']:
        score += 10
        strengths.append(f"学历优秀：{edu}")
    elif edu == '大专':
        score -= 5
        weaknesses.append("学历偏低")
    
    skills = candidate_data.get('skills', '')
    if len(skills) > 10:
        score += 5
        strengths.append("技能描述详细")
    
    company = candidate_data.get('company', '')
    big_tech = ['字节', '阿里', '腾讯', '百度', '美团', '京东', '华为', '微软', '谷歌']
    if any(bt in company for bt in big_tech):
        score += 5
        strengths.append("来自知名企业")
    
    if score > 85:
        growth_potential = "高"
    elif score > 70:
        growth_potential = "中"
    else:
        growth_potential = "低"
    
    if years < 2:
        risk_points.append("可能缺乏实际项目经验")
    if not skills:
        risk_points.append("技能描述不够详细")
    
    suitable_scenarios = ["通用岗位推荐"]
    if years >= 5:
        suitable_scenarios.append("高级职位推荐")
    if edu in ['硕士', '博士']:
        suitable_scenarios.append("技术专家岗位")
    
    return {
        "overall_score": min(score, 100),
        "skill_match_score": min(score + 5, 100),
        "experience_match_score": min(score, 100),
        "growth_potential": growth_potential,
        "risk_points": risk_points,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendation": f"该候选人综合评分{score}分，{growth_potential}成长潜力，{'建议重点关注' if score >= 80 else '建议综合考虑'}。",
        "suitable_scenarios": suitable_scenarios
    }

def generate_candidate_report(candidate_data, evaluation):
    """生成候选人优劣势报告"""
    report = f"""# 候选人评估报告

## 基本信息
| 项目 | 内容 |
|------|------|
| 姓名 | {candidate_data.get('name', '未知')} |
| 当前职位 | {candidate_data.get('position', '未知')} |
| 当前公司 | {candidate_data.get('company', '未知')} |
| 工作年限 | {candidate_data.get('years', 0)}年 |
| 学历 | {candidate_data.get('education', '未知')} |

## 综合评分
- **总体评分：{evaluation.get('overall_score', 0)}/100**
- 技能匹配度：{evaluation.get('skill_match_score', 0)}/100
- 经验匹配度：{evaluation.get('experience_match_score', 0)}/100
- 成长潜力：{evaluation.get('growth_potential', '中')}

## 核心优势
"""
    for strength in evaluation.get('strengths', []):
        report += f"- {strength}\n"
    
    if not evaluation.get('strengths'):
        report += "- 暂无明显优势记录\n"
    
    report += """
## 潜在风险
"""
    for risk in evaluation.get('risk_points', []):
        report += f"- ⚠️ {risk}\n"
    
    if not evaluation.get('risk_points'):
        report += "- 暂无明显风险\n"
    
    report += f"""
## 推荐理由
{evaluation.get('recommendation', '暂无')}

## 适合场景
"""
    for scenario in evaluation.get('suitable_scenarios', []):
        report += f"- {scenario}\n"
    
    if not evaluation.get('suitable_scenarios'):
        report += "- 通用场景\n"
    
    report += f"""
---
报告生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

def ai_generate_outreach_message(candidate_data, job_requirement, channel='email'):
    """AI生成个性化联系话术"""
    if not OPENAI_AVAILABLE:
        return generate_outreach_rule_based(candidate_data, job_requirement, channel)
    
    try:
        client = openai.OpenAI(
            api_key=CONFIG['deepseek']['api_key'],
            base_url=CONFIG['deepseek']['base_url']
        )
        
        channel_text = "邮件" if channel == 'email' else "微信"
        
        prompt = f"""请为以下候选人生成一封个性化的{channel_text}联系话术：

【候选人信息】
姓名：{candidate_data.get('name', '未知')}
当前职位：{candidate_data.get('position', '未知')}
当前公司：{candidate_data.get('company', '未知')}
技能：{candidate_data.get('skills', '未知')}

【目标岗位】
{job_requirement}

要求：
1. 语气专业、友好
2. 突出候选人优势与岗位的匹配点
3. {channel_text}长度适中（{channel_text}约200字以内）
4. 包含明确的行动召唤
5. 结尾附上联系方式占位符

请以JSON格式返回：
{{
    "subject": "邮件主题（仅邮件需要）",
    "message": "完整的{channel_text}内容",
    "key_points": ["强调的要点1", "要点2"],  // 话术中强调的关键点
    "personalization": "个性化亮点"  // 为什么这个候选人特别适合
}}

只返回JSON。"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的猎头顾问，擅长撰写吸引人的候选人联系话术。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        result = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            return json.loads(json_match.group())
        
        return generate_outreach_rule_based(candidate_data, job_requirement, channel)
        
    except Exception as e:
        print(f"AI outreach generation error: {e}")
        return generate_outreach_rule_based(candidate_data, job_requirement, channel)

def generate_outreach_rule_based(candidate_data, job_requirement, channel):
    """基于规则生成联系话术"""
    name = candidate_data.get('name', '您好')
    position = candidate_data.get('position', '')
    company = candidate_data.get('company', '')
    skills = candidate_data.get('skills', '')
    
    if channel == 'email':
        return {
            "subject": f"【职位推荐】{name}您好，有一个适合您的岗位机会",
            "message": f"""尊敬的{name}您好，

我是猎头顾问，看到您目前在{company}担任{position}，对您的背景非常感兴趣。

我们正在为一家知名企业寻访{job_requirement}方向的优秀人才，看到您的技能背景与这个岗位非常契合。

您是否方便进行一次简短的沟通？我可以详细介绍这个岗位的具体情况，同时了解您的职业发展需求。

期待您的回复！

Best regards,
猎头顾问
联系方式：[您的联系方式]""",
            "key_points": ["当前背景与岗位匹配", "知名企业机会", "专业猎头服务"],
            "personalization": f"基于您在{company}担任{position}的经验"
        }
    else:
        return {
            "subject": "",
            "message": f"""Hi {name}，看到您目前在{company}做{position}，您的{skills}背景和我们正在寻访的一个高端岗位很匹配~

方便的话可以聊聊？🙋""",
            "key_points": ["个人化开场", "突出匹配点", "简洁友好"],
            "personalization": f"您的{position}经验非常匹配"
        }


# ============ API 路由 ============

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('.', 'index.html')

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat(),
        'features': {
            'feishu': REQUESTS_AVAILABLE,
            'openai': OPENAI_AVAILABLE
        }
    })

@app.route('/api/candidates', methods=['GET', 'POST'])
def candidates():
    """候选人列表/新增"""
    if request.method == 'GET':
        # 尝试从飞书获取
        feishu_data = fetch_candidates_from_feishu()
        print(f'[DEBUG] fetch_candidates_from_feishu returned: {len(feishu_data) if feishu_data else 0} items')
        if feishu_data is not None and len(feishu_data) > 0:
            return jsonify(feishu_data)
        
        # 返回内存数据（仅作为降级）
        print('[DEBUG] Using memory data as fallback')
        return jsonify(DB['candidates'])
    
    elif request.method == 'POST':
        data = request.json
        
        # 检查去重
        phone_hash = hash_phone(data.get('phone', ''))
        email_hash = hash_email(data.get('email', ''))
        
        for c in DB['candidates']:
            if phone_hash and hash_phone(c.get('phone', '')) == phone_hash:
                return jsonify({'error': '候选人已存在（手机号重复）', 'existing_id': c['id']}), 400
            if email_hash and hash_email(c.get('email', '')) == email_hash:
                return jsonify({'error': '候选人已存在（邮箱重复）', 'existing_id': c['id']}), 400
        
        # AI 评分
        data['score'] = calculate_score(data)
        
        # AI 画像
        data['profile'] = generate_ai_profile(data)
        
        # 保存到飞书
        saved, record_id = save_candidate_to_feishu(data)
        
        # 保存到内存
        candidate = {
            'id': generate_id(),
            'name': data.get('name', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'company': data.get('company', ''),
            'position': data.get('position', ''),
            'years': data.get('years', 0),
            'education': data.get('education', ''),
            'skills': data.get('skills', ''),
            'profile': data.get('profile', ''),
            'score': data.get('score', 0),
            'source': data.get('source', ''),
            'status': 'PENDING',
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        if saved and record_id:
            candidate['id'] = record_id
        
        DB['candidates'].append(candidate)
        
        return jsonify(candidate), 201

@app.route('/api/candidates/<candidate_id>')
def get_candidate(candidate_id):
    """获取单个候选人"""
    for c in DB['candidates']:
        if c['id'] == candidate_id:
            return jsonify(c)
    return jsonify({'error': 'Candidate not found'}), 404

@app.route('/api/candidates/<candidate_id>', methods=['PUT'])
def update_candidate(candidate_id):
    """更新候选人"""
    data = request.json
    for i, c in enumerate(DB['candidates']):
        if c['id'] == candidate_id:
            DB['candidates'][i].update(data)
            return jsonify(DB['candidates'][i])
    return jsonify({'error': 'Candidate not found'}), 404

@app.route('/api/candidates/<candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    """删除候选人"""
    for i, c in enumerate(DB['candidates']):
        if c['id'] == candidate_id:
            DB['candidates'].pop(i)
            return jsonify({'success': True})
    return jsonify({'error': 'Candidate not found'}), 404

@app.route('/api/candidates/similar/<candidate_id>')
def find_similar(candidate_id):
    """查找相似候选人"""
    target = None
    for c in DB['candidates']:
        if c['id'] == candidate_id:
            target = c
            break
    
    if not target:
        return jsonify({'error': 'Candidate not found'}), 404
    
    similarities = []
    for c in DB['candidates']:
        if c['id'] == candidate_id:
            continue
        
        similarity = calculate_similarity(target, c)
        
        # 找出共同技能
        target_skills = set(s.strip().lower() for s in target.get('skills', '').split(','))
        c_skills = set(s.strip().lower() for s in c.get('skills', '').split(','))
        matched = list(target_skills & c_skills)
        
        similarities.append({
            **c,
            'similarity': similarity,
            'matched_skills': matched
        })
    
    # 按相似度排序
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify(similarities[:10])

@app.route('/api/candidates/dedup')
def deduplicate():
    """候选人去重检测"""
    seen = {}
    duplicates = []
    
    for c in DB['candidates']:
        phone_hash = hash_phone(c.get('phone', ''))
        email_hash = hash_email(c.get('email', ''))
        
        key = (phone_hash, email_hash)
        if key in seen:
            duplicates.append({
                'original': seen[key],
                'duplicate': c['id']
            })
        else:
            seen[key] = c['id']
    
    return jsonify({
        'total': len(DB['candidates']),
        'unique': len(DB['candidates']) - len(duplicates),
        'duplicates': duplicates
    })

@app.route('/api/parse-resume-text', methods=['POST'])
def parse_resume_text():
    """AI简历解析（文本方式）"""
    data = request.json
    resume_text = data.get('resume_text', '')
    
    if not resume_text:
        return jsonify({'error': 'No resume text provided'}), 400
    
    result = parse_resume_with_ai(resume_text)
    
    # 计算能力评分
    result['score'] = calculate_score(result)
    
    # 生成画像
    result['profile'] = generate_ai_profile(result)
    
    return jsonify(result)

@app.route('/api/parse-file', methods=['POST'])
def parse_file():
    """解析上传的简历文件"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # 读取文件内容
    try:
        content = file.read().decode('utf-8')
    except:
        content = file.read().decode('gbk', errors='ignore')
    
    result = parse_resume_with_ai(content)
    result['score'] = calculate_score(result)
    result['profile'] = generate_ai_profile(result)
    
    return jsonify(result)

@app.route('/api/parse-resume', methods=['POST'])
def parse_resume_file():
    """解析上传的简历文件（支持PDF、Word、图片）"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
    filename = request.form.get('fileName', file.filename)
    
    # 读取文件内容
    resume_text = ''
    file_content = file.read()
    
    # 检查文件类型
    filename_lower = filename.lower() if filename else ''
    
    if filename_lower.endswith('.pdf'):
        # PDF文件处理
        text, error = extract_text_from_pdf(file_content)
        if error:
            return jsonify({'error': f'PDF解析失败: {error}'}), 400
        resume_text = text
    else:
        # 其他文件尝试文本解码
        try:
            try:
                resume_text = file_content.decode('utf-8')
            except:
                try:
                    resume_text = file_content.decode('gbk', errors='ignore')
                except:
                    resume_text = str(file_content)
        except Exception as e:
            return jsonify({'error': f'文件读取失败: {str(e)}'}), 400
    
    if not resume_text or not resume_text.strip():
        return jsonify({'error': '文件内容为空或无法解析'}), 400
    
    # 使用AI解析
    result = parse_resume_with_ai(resume_text)
    
    # 计算能力评分
    result['score'] = calculate_score(result)
    
    # 生成画像
    result['profile'] = generate_ai_profile(result)
    
    # 添加文件名信息
    result['source_file'] = filename
    
    return jsonify({
        'success': True,
        'data': result,
        'rawText': f'已从文件 {filename} 中提取简历信息，AI解析完成。'
    })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': f'解析失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/save-candidate', methods=['POST'])
def save_candidate_api():
    """保存候选人到飞书多维表格"""
    data = request.json
    
    # 准备候选人数据
    candidate_data = {
        'name': data.get('name', ''),
        'phone': data.get('phone', ''),
        'email': data.get('email', ''),
        'company': data.get('company', ''),
        'position': data.get('position', ''),
        'years': data.get('years', 0),
        'education': data.get('education', ''),
        'skills': data.get('skills', []) if isinstance(data.get('skills', []), list) else ','.join(data.get('skills', [])),
        'source': data.get('source', ''),
        'score': data.get('score', 0),
        'profile': data.get('profile', '')
    }
    
    # 计算评分（如果没有提供）
    if not candidate_data['score'] or candidate_data['score'] == 0:
        candidate_data['score'] = calculate_score(candidate_data)
    
    # 生成画像（如果没有提供）
    if not candidate_data['profile']:
        candidate_data['profile'] = generate_ai_profile(candidate_data)
    
    # 检查去重
    phone_hash = hash_phone(candidate_data['phone'])
    email_hash = hash_email(candidate_data['email'])
    
    for c in DB['candidates']:
        if phone_hash and hash_phone(c.get('phone', '')) == phone_hash:
            return jsonify({
                'success': False, 
                'error': '候选人已存在（手机号重复）',
                'existing_id': c['id']
            }), 400
        if email_hash and hash_email(c.get('email', '')) == email_hash:
            return jsonify({
                'success': False,
                'error': '候选人已存在（邮箱重复）',
                'existing_id': c['id']
            }), 400
    
    # 使用前端提供的飞书配置（优先）或默认配置
    app_token = data.get('appToken', CONFIG['feishu']['app_token'])
    table_id = data.get('tableId', CONFIG['feishu']['table_id'])
    app_secret = data.get('appSecret', CONFIG['feishu'].get('app_secret', ''))
    
    # 临时更新配置
    original_app_token = CONFIG['feishu']['app_token']
    original_table_id = CONFIG['feishu']['table_id']
    original_app_secret = CONFIG['feishu'].get('app_secret', '')
    
    if app_token:
        CONFIG['feishu']['app_token'] = app_token
    if table_id:
        CONFIG['feishu']['table_id'] = table_id
    if app_secret:
        CONFIG['feishu']['app_secret'] = app_secret
    
    try:
        # 保存到飞书
        saved, record_id = save_candidate_to_feishu(candidate_data)
        
        # 保存到内存
        candidate = {
            'id': generate_id(),
            'name': candidate_data['name'],
            'phone': candidate_data['phone'],
            'email': candidate_data['email'],
            'company': candidate_data['company'],
            'position': candidate_data['position'],
            'years': candidate_data['years'],
            'education': candidate_data['education'],
            'skills': candidate_data['skills'],
            'profile': candidate_data['profile'],
            'score': candidate_data['score'],
            'source': candidate_data['source'],
            'status': 'PENDING',
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        if saved and record_id:
            candidate['id'] = record_id
        
        DB['candidates'].append(candidate)
        
        return jsonify({
            'success': True,
            'data': candidate,
            'record_id': record_id
        })
        
    except Exception as e:
        print(f"Error saving candidate: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        # 恢复原始配置
        CONFIG['feishu']['app_token'] = original_app_token
        CONFIG['feishu']['table_id'] = original_table_id
        if original_app_secret:
            CONFIG['feishu']['app_secret'] = original_app_secret

@app.route('/api/interviews', methods=['GET', 'POST'])
def interviews():
    """面试记录"""
    if request.method == 'GET':
        return jsonify(DB['interviews'])
    
    data = request.json
    interview = {
        'id': generate_id(),
        'candidate_id': data.get('candidate_id', ''),
        'candidate_name': data.get('candidate_name', ''),
        'position': data.get('position', ''),
        'round': data.get('round', ''),
        'interviewer': data.get('interviewer', ''),
        'date': data.get('date', ''),
        'status': data.get('status', '待评价'),
        'notes': data.get('notes', ''),
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    DB['interviews'].append(interview)
    return jsonify(interview), 201

@app.route('/api/reminders', methods=['GET', 'POST'])
def reminders():
    """提醒列表/新增"""
    if request.method == 'GET':
        return jsonify(DB['reminders'])
    
    data = request.json
    reminder = {
        'id': generate_id(),
        'candidate_id': data.get('candidate_id', ''),
        'title': data.get('title', ''),
        'type': data.get('type', 'followup'),
        'time': data.get('time', ''),
        'status': 'pending',
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d')
    }
    
    DB['reminders'].append(reminder)
    return jsonify(reminder), 201

@app.route('/api/companies')
def companies():
    """公司列表"""
    return jsonify(DB['companies'])

@app.route('/api/companies/<company_id>/candidates')
def company_candidates(company_id):
    """公司候选人列表"""
    company = next((c for c in DB['companies'] if c['id'] == company_id), None)
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    candidates = [c for c in DB['candidates'] if c.get('company') == company['name']]
    return jsonify(candidates)

@app.route('/api/stats')
def stats():
    """统计数据"""
    total = len(DB['candidates'])
    active = len([c for c in DB['candidates'] if c.get('status') == 'ACTIVE'])
    interview = len([c for c in DB['candidates'] if c.get('status') == 'INTERVIEW'])
    pending = len([c for c in DB['candidates'] if c.get('status') == 'PENDING'])
    
    avg_score = 0
    if DB['candidates']:
        avg_score = sum(c.get('score', 0) for c in DB['candidates']) / total
    
    return jsonify({
        'total_candidates': total,
        'active': active,
        'in_interview': interview,
        'pending': pending,
        'avg_score': round(avg_score, 1),
        'total_interviews': len(DB['interviews']),
        'pending_reminders': len([r for r in DB['reminders'] if r.get('status') == 'pending'])
    })

# ============ AI 初级搜寻员 API ============

@app.route('/api/smart-search', methods=['POST'])
def api_smart_search():
    """智能搜索相似候选人"""
    data = request.json
    job_requirement = data.get('job_requirement', '')
    
    if not job_requirement:
        return jsonify({'error': '请输入岗位需求'}), 400
    
    # 从飞书获取真实候选人数据
    candidates = fetch_candidates_from_feishu()
    if not candidates:
        candidates = DB['candidates']
    
    # AI分析岗位需求
    search_analysis = ai_smart_search(job_requirement)
    search_conditions = search_analysis.get('search_conditions', {})
    
    # 在候选人库中搜索
    results = []
    for candidate in candidates:
        match_result = calculate_match_score(candidate, search_conditions)
        
        if match_result['total_score'] > 30:  # 过滤低分候选人
            results.append({
                **candidate,
                'match_score': match_result['total_score'],
                'matched_skills': match_result['matched_skills'],
                'missing_skills': match_result['missing_skills'],
                'match_reasons': match_result['match_reasons'],
                'match_details': {
                    'skill_score': match_result['skill_score'],
                    'experience_score': match_result['experience_score'],
                    'industry_score': match_result['industry_score'],
                    'education_score': match_result['education_score']
                }
            })
    
    # 按匹配度排序
    results.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify({
        'success': True,
        'job_requirement': job_requirement,
        'analysis': search_analysis,
        'recommendations': results[:10],  # 返回Top10
        'total_found': len(results)
    })

@app.route('/api/evaluate-candidate', methods=['POST'])
def api_evaluate_candidate():
    """AI评估候选人适合度"""
    data = request.json
    candidate_id = data.get('candidate_id')
    job_requirement = data.get('job_requirement', '')
    
    if not candidate_id:
        return jsonify({'error': '请选择候选人'}), 400
    
    # 从飞书获取真实候选人数据
    candidates = fetch_candidates_from_feishu()
    if not candidates:
        candidates = DB['candidates']
    
    # 获取候选人信息
    candidate = None
    for c in candidates:
        if c['id'] == candidate_id:
            candidate = c
            break
    
    if not candidate:
        return jsonify({'error': '候选人未找到'}), 404
    
    # AI评估
    evaluation = ai_evaluate_candidate(candidate, job_requirement)
    
    return jsonify({
        'success': True,
        'candidate': candidate,
        'job_requirement': job_requirement,
        'evaluation': evaluation
    })

@app.route('/api/generate-report', methods=['POST'])
def api_generate_report():
    """生成候选人优劣势报告"""
    data = request.json
    candidate_id = data.get('candidate_id')
    job_requirement = data.get('job_requirement', '')
    format_type = data.get('format', 'markdown')
    
    if not candidate_id:
        return jsonify({'error': '请选择候选人'}), 400
    
    # 从飞书获取真实候选人数据
    candidates = fetch_candidates_from_feishu()
    if not candidates:
        candidates = DB['candidates']
    
    # 获取候选人信息
    candidate = None
    for c in candidates:
        if c['id'] == candidate_id:
            candidate = c
            break
    
    if not candidate:
        return jsonify({'error': '候选人未找到'}), 404
    
    # AI评估
    evaluation = ai_evaluate_candidate(candidate, job_requirement)
    
    # 生成报告
    report = generate_candidate_report(candidate, evaluation)
    
    return jsonify({
        'success': True,
        'candidate': candidate,
        'evaluation': evaluation,
        'report': report,
        'format': format_type
    })

@app.route('/api/generate-outreach', methods=['POST'])
def api_generate_outreach():
    """AI生成个性化联系话术"""
    data = request.json
    candidate_ids = data.get('candidate_ids', [])
    job_requirement = data.get('job_requirement', '')
    channel = data.get('channel', 'email')  # email 或 wechat
    
    if not candidate_ids:
        return jsonify({'error': '请选择候选人'}), 400
    
    # 从飞书获取真实候选人数据
    all_candidates = fetch_candidates_from_feishu()
    if not all_candidates:
        all_candidates = DB['candidates']
    
    results = []
    for candidate_id in candidate_ids:
        # 获取候选人信息
        candidate = None
        for c in all_candidates:
            if c['id'] == candidate_id:
                candidate = c
                break
        
        if candidate:
            message = ai_generate_outreach_message(candidate, job_requirement, channel)
            results.append({
                'candidate_id': candidate_id,
                'candidate_name': candidate.get('name', '未知'),
                **message
            })
    
    return jsonify({
        'success': True,
        'channel': channel,
        'job_requirement': job_requirement,
        'messages': results,
        'count': len(results)
    })

@app.route('/api/send-batch', methods=['POST'])
def api_send_batch():
    """批量发送话术（模拟）"""
    data = request.json
    messages = data.get('messages', [])
    channel = data.get('channel', 'email')
    
    # 模拟发送
    sent = []
    failed = []
    
    for msg in messages:
        # 实际项目中，这里应该调用邮件/微信API
        # 暂时模拟成功
        try:
            sent.append({
                'candidate_id': msg.get('candidate_id'),
                'candidate_name': msg.get('candidate_name'),
                'status': 'sent',
                'sent_at': datetime.datetime.now().isoformat()
            })
        except Exception as e:
            failed.append({
                'candidate_id': msg.get('candidate_id'),
                'candidate_name': msg.get('candidate_name'),
                'status': 'failed',
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'channel': channel,
        'sent': sent,
        'failed': failed,
        'total_sent': len(sent),
        'total_failed': len(failed)
    })


# ============ 原有配置 API ============

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """系统配置"""
    if request.method == 'GET':
        return jsonify({
            'feishu': {
                'app_token': CONFIG['feishu']['app_token'],
                'table_id': CONFIG['feishu']['table_id']
            }
        })
    
    data = request.json
    if 'feishu' in data:
        CONFIG['feishu']['app_token'] = data['feishu'].get('app_token', CONFIG['feishu']['app_token'])
        CONFIG['feishu']['table_id'] = data['feishu'].get('table_id', CONFIG['feishu']['table_id'])
    
    if 'deepseek' in data:
        CONFIG['deepseek']['api_key'] = data['deepseek'].get('api_key', CONFIG['deepseek']['api_key'])
    
    return jsonify({'success': True})

# ============ 启动 ============

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║             Talent AI - 智能猎头系统                          ║
║             AI初级搜寻员 v1.0                                 ║
╠═══════════════════════════════════════════════════════════════╣
║  🌐 访问地址: http://localhost:{port}                          ║
╠═══════════════════════════════════════════════════════════════╣
║  📋 核心功能:                                                ║
║  ┌─────────────────────────────────────────────────────────┐   ║
║  │  模块1: 智能推荐 - 一句话找人才，防丢单                  │   ║
║  │  模块2: AI评估 - 智能判断候选人与岗位匹配度              │   ║
║  │  模块3: 优劣势报告 - 专业推荐分析报告                   │   ║
║  │  模块4: 定制化群发 - AI生成个性化联系话术               │   ║
║  └─────────────────────────────────────────────────────────┘   ║
╠═══════════════════════════════════════════════════════════════╣
║  🔧 基础功能:                                                 ║
║  ✓ 候选人管理 (CRUD)                                        ║
║  ✓ AI简历解析 (单个/批量)                                    ║
║  ✓ ZIP批量上传                                               ║
║  ✓ 候选人去重                                                ║
║  ✓ 相似度推荐                                                ║
║  ✓ 能力评分                                                  ║
║  ✓ 画像生成                                                   ║
║  ✓ 面试进度跟踪                                              ║
║  ✓ 飞书多维表格集成                                          ║
║  ✓ DeepSeek AI解析                                          ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
