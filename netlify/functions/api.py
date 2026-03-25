import sys
import os

# 确保项目根目录在 sys.path 中，以便导入 algorithm 和 web_app
# 在 Netlify 环境中，functions 目录通常被打包，我们需要确保路径正确
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import aws_lambda_wsgi
from web_app.app import app

def handler(event, context):
    # aws-lambda-wsgi 将 AWS Lambda (Netlify) 的事件转换为 WSGI 格式供 Flask 使用
    return aws_lambda_wsgi.response(app, event, context)
