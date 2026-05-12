# ============================================================
# 脚本名称：alert_query_api.py
# 所属系统：00杰哥系统总管
# 功能描述：提供异常事件查询的HTTP接口，供系统管家调用
# 创建日期：2026-05-10
# 修正记录：2026-05-10 修复UTF-8 BOM文件读取问题
# 调用方式：GET /alerts?days=1
# 返回格式：JSON {"summary": "...", "alerts": [...]}
# ============================================================
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, glob
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

EVT_DIR = r"D:\杰哥智能化系统\00杰哥系统总管\04日志\血脉分钟级监测\异常事件"

def get_alerts(days=1):
    if not os.path.exists(EVT_DIR): return [], "异常事件目录不存在"
    today = datetime.now()
    start_date = today - timedelta(days=days)
    alerts = []
    for fpath in glob.glob(os.path.join(EVT_DIR, "EVT-*.json")):
        fname = os.path.basename(fpath)
        try:
            file_date = datetime.strptime(fname[4:12], "%Y%m%d")
        except:
            continue
        if file_date < start_date: continue
        # 使用 utf-8-sig 自动处理 BOM 头部
        with open(fpath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            alerts.append({"file": fname, "date": file_date.strftime("%Y-%m-%d"), "content": data})
    alerts.sort(key=lambda x: x['date'], reverse=True)
    today_alerts = sum(1 for a in alerts if a['date'] == today.strftime("%Y-%m-%d"))
    summary = f"最近{days}天共 {len(alerts)} 条异常，今天 {today_alerts} 条。"
    return alerts, summary

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if '/alerts' not in self.path:
            self.send_error(404)
            return
        params = parse_qs(urlparse(self.path).query)
        days = int(params.get('days', [1])[0])
        alerts, summary = get_alerts(days)
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({"summary": summary, "alerts": alerts}, ensure_ascii=False).encode('utf-8'))

def run_server(port=5802):
    httpd = HTTPServer(('127.0.0.1', port), Handler)
    print(f"报警查询API已启动，监听地址：127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
