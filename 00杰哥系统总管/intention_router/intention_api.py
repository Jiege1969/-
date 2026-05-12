# ============================================================
# 脚本名称：intention_api.py
# 所属系统：00杰哥系统总管 / 意图归因器
# 功能描述：基于本地Ollama的公共意图归因API微服务。
#           接收用户消息，返回标准路由指令JSON。
# 创建日期：2026-05-10
# 监听端口：5801
# 接口：POST /classify
#       请求体：{"message": "用户消息"}
#       返回：{"target_robot": "...", "refined_query": "...", "fallback_msg": "..."}
# 依赖：Ollama服务已启动，模型已就绪（qwen2.5:7b）
# 调用示例（PowerShell）：
#   Invoke-RestMethod -Uri http://localhost:5801/classify -Method POST -Body '{"message":"你好"}' -ContentType "application/json; charset=utf-8"
# ============================================================

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import sys
import os

# ------------------------------
# 配置区（已根据扫描结果修正）
# ------------------------------
OLLAMA_API_URL = "http://localhost:29134/api/generate"
# 使用已验证的 qwen2.5:7b，能完美执行意图分类任务
MODEL_NAME = "qwen2.5:7b"

# 读取同目录下的意图分类提示词
PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intention_prompt.txt")
try:
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()
except Exception as e:
    print(f"错误：无法读取提示词文件 {PROMPT_FILE}: {e}")
    sys.exit(1)

class ClassifierHandler(BaseHTTPRequestHandler):
    """意图归因请求处理器"""
    
    def do_POST(self):
        if self.path != '/classify':
            self.send_error(404)
            return

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, "Empty body")
            return

        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
            user_message = data.get('message', '')
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        # 调用Ollama进行分类
        payload = {
            "model": MODEL_NAME,
            "system": SYSTEM_PROMPT,
            "prompt": f"用户消息：{user_message}",
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,     # 微调至 0.1，确保稳定且高效
                "num_predict": 512      # 增大到 512，确保JSON不截断
            }
        }
        
        try:
            resp = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
            resp.raise_for_status()
            resp_json = resp.json()
            raw_response = resp_json.get('response', '').strip()
            
            # 安全提取JSON部分
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                route_cmd = json.loads(raw_response[json_start:json_end])
            else:
                raise ValueError("未找到有效JSON格式")
                
        except Exception as e:
            # 异常兜底
            route_cmd = {
                "target_robot": "default",
                "refined_query": "",
                "fallback_msg": "杰哥，我暂时无法理解你的意图。建议您直接找‘系统管家’帮忙：【向系统管家提问】"
            }

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(route_cmd, ensure_ascii=False).encode('utf-8'))
        return

def run_server(port=5801):
    """启动HTTP服务"""
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, ClassifierHandler)
    print(f'意图归因API服务已启动，监听地址：127.0.0.1:{port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n服务已停止')
        httpd.server_close()

if __name__ == '__main__':
    run_server()
