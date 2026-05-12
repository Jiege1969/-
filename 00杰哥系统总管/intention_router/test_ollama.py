import requests, json
prompt_file = r"D:\杰哥智能化系统\00杰哥系统总管\intention_router\intention_prompt.txt"
with open(prompt_file, 'r', encoding='utf-8') as f:
    system_prompt = f.read()

payload = {
    "model": "qwen3:14b",
    "system": system_prompt,
    "prompt": "用户消息：帮我看看腾讯今天涨了没",
    "format": "json",
    "stream": False,
    "options": {"temperature": 0.0, "num_predict": 256}
}

try:
    resp = requests.post("http://localhost:29134/api/generate", json=payload, timeout=60)
    print("=== Ollama HTTP状态码 ===")
    print(resp.status_code)
    print("=== Ollama原始返回 ===")
    print(resp.text)
    data = resp.json()
    if 'response' in data:
        print("=== 模型回答 ===")
        print(data['response'])
    elif 'error' in data:
        print("!!! 模型返回错误:", data['error'])
except Exception as e:
    print("!!! 请求异常:", str(e))
