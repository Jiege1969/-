import requests, json

prompt_file = r"D:\杰哥智能化系统\00杰哥系统总管\intention_router\intention_prompt.txt"
with open(prompt_file, 'r', encoding='utf-8') as f:
    system_prompt = f.read()

models_to_test = ["qwen3:14b", "qwen2.5:7b"]

for model in models_to_test:
    print(f"\n========== 测试模型: {model} ==========")
    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": "用户消息：帮我看看腾讯今天涨了没",
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 512}
    }
    try:
        resp = requests.post("http://localhost:29134/api/generate", json=payload, timeout=60)
        data = resp.json()
        if 'response' in data:
            print("回答:", data['response'])
        elif 'error' in data:
            print("错误:", data['error'])
    except Exception as e:
        print("异常:", str(e))
