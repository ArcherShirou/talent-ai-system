#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Talent AI - 智能猎头系统
组织架构可视化 + 人才Mapping + AI简历解析
"""

import os
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# 配置 - 使用环境变量
CONFIG = {
    'deepseek': {
        'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
        'base_url': 'https://api.deepseek.com/v1'
    },
    'feishu': {
        'app_id': os.getenv('FEISHU_APP_ID', ''),
        'app_secret': os.getenv('FEISHU_APP_SECRET', ''),
        'app_token': os.getenv('FEISHU_APP_TOKEN', '')
    }
}

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "Talent AI"})

@app.route('/api/companies')
def get_companies():
    """获取公司列表及候选人统计"""
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Talent AI 运行在 http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)