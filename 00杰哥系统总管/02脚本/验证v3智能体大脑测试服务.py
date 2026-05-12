"""
名称：验证v3智能体大脑测试服务.py
作用：验证 v3 智能体大脑测试服务的健康检查、模型列表、任务识别、模型路由、能力规划、知识库接口、工作流规划、股票研究、视频制作、本职工作、税收业务接口和真实推理接口。
触发方式：python 验证v3智能体大脑测试服务.py
依赖：Python 标准库；目标服务需监听 127.0.0.1:28100。
所属系统：00杰哥系统总管
安全边界：只访问本机 v3 测试端口，只在 v3 日志目录写入验证结果，不修改生产服务。
创建/修改记录：2026-04-26 创建第一阶段接口验证脚本；将 POST 验证等待时间调整为按请求负载中的超时类数值自适应，避免模型冷启动造成误判。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request


BASE_URL = "http://127.0.0.1:28100"


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def log_dir() -> Path:
    target = v3_root() / "01杰哥智能系统" / "04日志" / "agent-brain-test"
    target.mkdir(parents=True, exist_ok=True)
    return target


def get_json(path: str) -> dict[str, Any]:
    with request.urlopen(BASE_URL + path, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=True).encode("ascii")
    req = request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    numeric_limits = [int(value) for value in payload.values() if isinstance(value, int)]
    request_timeout = max(10, min(300, max(numeric_limits, default=10)))
    with request.urlopen(req, timeout=request_timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def main() -> int:
    text_key = "\u6587\u672c"
    stock_text = "\u8bf7\u5206\u6790\u8d35\u5dde\u8305\u53f0\u6700\u65b0\u8d22\u62a5\u548c\u4f30\u503c\u98ce\u9669"
    code_text = "\u5e2e\u6211\u5199\u4e00\u4e2aDocker\u5065\u5eb7\u68c0\u67e5\u811a\u672c\u5e76\u89e3\u91ca\u98ce\u9669"
    think_text = "\u7528\u4e00\u53e5\u8bdd\u8bf4\u660e\u6770\u54e5\u667a\u80fd\u5316\u7cfb\u7edfv3\u7684\u4f5c\u7528\u3002"
    ops_text = "\u8bf7\u68c0\u67e5\u7cfb\u7edf\u72b6\u6001\u5e76\u505c\u6b62\u5f02\u5e38\u670d\u52a1"
    tax_text = "\u8bf7\u5206\u7c7b\u8fd9\u4e2a\u589e\u503c\u7a0e\u4e1a\u52a1\u5e76\u5217\u51fa\u6240\u5f97\u7a0e\u98ce\u9669"
    max_output_key = "\u6700\u5927\u8f93\u51fa"
    timeout_key = "\u8d85\u65f6\u79d2"

    health = get_json("/health")
    models = get_json("/%E6%A8%A1%E5%9E%8B/%E5%88%97%E8%A1%A8")
    kb_status = get_json("/%E7%9F%A5%E8%AF%86%E5%BA%93/%E7%8A%B6%E6%80%81")
    stock_status = get_json("/%E8%82%A1%E7%A5%A8%E7%A0%94%E7%A9%B6/%E7%8A%B6%E6%80%81")
    stock_plan = get_json("/%E8%82%A1%E7%A5%A8%E7%A0%94%E7%A9%B6/%E8%AE%A1%E5%88%92")
    stock_report = get_json("/%E8%82%A1%E7%A5%A8%E7%A0%94%E7%A9%B6/%E6%8A%A5%E5%91%8A")
    stock_risk = get_json("/%E8%82%A1%E7%A5%A8%E7%A0%94%E7%A9%B6/%E9%A3%8E%E9%99%A9%E6%91%98%E8%A6%81")
    video_status = get_json("/%E8%A7%86%E9%A2%91%E5%88%B6%E4%BD%9C/%E7%8A%B6%E6%80%81")
    video_plan = get_json("/%E8%A7%86%E9%A2%91%E5%88%B6%E4%BD%9C/%E8%AE%A1%E5%88%92")
    video_script = get_json("/%E8%A7%86%E9%A2%91%E5%88%B6%E4%BD%9C/%E8%84%9A%E6%9C%AC%E8%8D%89%E7%A8%BF")
    video_storyboard = get_json("/%E8%A7%86%E9%A2%91%E5%88%B6%E4%BD%9C/%E5%88%86%E9%95%9C%E8%AE%A1%E5%88%92")
    work_status = get_json("/%E6%9C%AC%E8%81%8C%E5%B7%A5%E4%BD%9C/%E7%8A%B6%E6%80%81")
    work_plan = get_json("/%E6%9C%AC%E8%81%8C%E5%B7%A5%E4%BD%9C/%E8%AE%A1%E5%88%92")
    work_draft = get_json("/%E6%9C%AC%E8%81%8C%E5%B7%A5%E4%BD%9C/%E8%8D%89%E7%A8%BF%E6%A1%86%E6%9E%B6")
    tax_status = get_json("/%E7%A8%8E%E6%94%B6%E4%B8%9A%E5%8A%A1/%E7%8A%B6%E6%80%81")
    tax_index = get_json("/%E7%A8%8E%E6%94%B6%E4%B8%9A%E5%8A%A1/%E5%88%86%E7%B1%BB%E7%B4%A2%E5%BC%95")
    tax_policy_case_index = get_json("/%E7%A8%8E%E6%94%B6%E4%B8%9A%E5%8A%A1/%E6%94%BF%E7%AD%96%E6%A1%88%E4%BE%8B%E7%B4%A2%E5%BC%95")
    tax_plan = get_json("/%E7%A8%8E%E6%94%B6%E4%B8%9A%E5%8A%A1/%E5%A4%84%E7%90%86%E8%AE%A1%E5%88%92")
    task = post_json("/%E4%BB%BB%E5%8A%A1%E8%AF%86%E5%88%AB", {text_key: stock_text})
    route = post_json("/%E6%A8%A1%E5%9E%8B/%E9%80%89%E6%8B%A9", {text_key: code_text})
    ability = post_json("/%E8%83%BD%E5%8A%9B/%E8%A7%84%E5%88%92", {text_key: stock_text})
    tax_task = post_json("/%E4%BB%BB%E5%8A%A1%E8%AF%86%E5%88%AB", {text_key: tax_text})
    tax_ability = post_json("/%E8%83%BD%E5%8A%9B/%E8%A7%84%E5%88%92", {text_key: tax_text})
    tax_workflow = post_json("/%E5%B7%A5%E4%BD%9C%E6%B5%81/%E8%A7%84%E5%88%92", {text_key: tax_text})
    ops_ability = post_json("/%E8%83%BD%E5%8A%9B/%E8%A7%84%E5%88%92", {text_key: ops_text})
    kb_search = post_json("/%E7%9F%A5%E8%AF%86%E5%BA%93/%E6%A3%80%E7%B4%A2", {"query": "v3", "limit": 3})
    workflow = post_json("/%E5%B7%A5%E4%BD%9C%E6%B5%81/%E8%A7%84%E5%88%92", {text_key: stock_text})
    think = post_json("/%E6%80%9D%E8%80%83", {text_key: think_text, max_output_key: 256, timeout_key: 240})

    checks = [
        assert_true("健康检查", health.get("状态") == "正常", health),
        assert_true("模型列表", models.get("Ollama", {}).get("模型数量", 0) >= 1, models.get("Ollama", {})),
        assert_true(
            "知识库状态",
            kb_status.get("知识库", {}).get("状态") == "正常",
            kb_status.get("知识库", {}),
        ),
        assert_true(
            "股票研究状态",
            stock_status.get("股票研究", {}).get("状态") == "正常",
            stock_status.get("股票研究", {}),
        ),
        assert_true(
            "股票研究计划",
            "任务列表" in stock_plan.get("研究计划", {}),
            stock_plan.get("研究计划", {}),
        ),
        assert_true(
            "股票研究报告",
            stock_report.get("研究报告", {}).get("状态") == "正常"
            and "不构成投资建议" in stock_report.get("研究报告", {}).get("内容", ""),
            {"状态": stock_report.get("研究报告", {}).get("状态")},
        ),
        assert_true(
            "股票风险摘要",
            "固定提示" in stock_risk.get("风险摘要", {}),
            stock_risk.get("风险摘要", {}),
        ),
        assert_true(
            "视频制作状态",
            video_status.get("视频制作", {}).get("状态") == "正常",
            video_status.get("视频制作", {}),
        ),
        assert_true(
            "视频制作计划",
            "任务列表" in video_plan.get("视频制作计划", {}),
            video_plan.get("视频制作计划", {}),
        ),
        assert_true(
            "视频脚本草稿",
            "脚本结构" in video_script.get("脚本草稿", {}),
            video_script.get("脚本草稿", {}),
        ),
        assert_true(
            "视频分镜计划",
            "镜头" in video_storyboard.get("分镜计划", {}),
            video_storyboard.get("分镜计划", {}),
        ),
        assert_true(
            "本职工作状态",
            work_status.get("本职工作", {}).get("状态") == "正常",
            work_status.get("本职工作", {}),
        ),
        assert_true(
            "本职工作计划",
            "任务列表" in work_plan.get("办公材料计划", {}),
            work_plan.get("办公材料计划", {}),
        ),
        assert_true(
            "本职工作草稿框架",
            "草稿模板" in work_draft.get("草稿框架", {}),
            work_draft.get("草稿框架", {}),
        ),
        assert_true(
            "税收业务状态",
            tax_status.get("税收业务", {}).get("状态") == "正常",
            tax_status.get("税收业务", {}),
        ),
        assert_true(
            "税收分类索引",
            "税种分类" in tax_index.get("分类索引", {}),
            tax_index.get("分类索引", {}),
        ),
        assert_true(
            "税收政策案例索引",
            "政策文件" in tax_policy_case_index.get("政策案例索引", {})
            and "业务案例" in tax_policy_case_index.get("政策案例索引", {}),
            tax_policy_case_index.get("政策案例索引", {}),
        ),
        assert_true(
            "税收处理计划",
            "处理流程" in tax_plan.get("处理计划", {}),
            tax_plan.get("处理计划", {}),
        ),
        assert_true("股票任务识别", task.get("结果", {}).get("任务类型") == "股票研究", task.get("结果", {})),
        assert_true("税收任务识别", tax_task.get("结果", {}).get("任务类型") == "税收业务", tax_task.get("结果", {})),
        assert_true(
            "代码模型路由",
            route.get("模型路由结果", {}).get("首选模型") == "qwen3-coder:30b",
            route.get("模型路由结果", {}),
        ),
        assert_true(
            "股票能力规划",
            ability.get("能力规划结果", {}).get("能力名") == "股票研究"
            and "股票研究系统" in ability.get("能力规划结果", {}).get("归属系统", ""),
            ability.get("能力规划结果", {}),
        ),
        assert_true(
            "税收能力规划",
            tax_ability.get("能力规划结果", {}).get("能力名") == "税收业务"
            and tax_ability.get("能力规划结果", {}).get("需要人工确认") is True,
            tax_ability.get("能力规划结果", {}),
        ),
        assert_true(
            "高风险能力确认",
            ops_ability.get("能力规划结果", {}).get("需要人工确认") is True,
            ops_ability.get("能力规划结果", {}),
        ),
        assert_true(
            "知识库检索",
            kb_search.get("检索结果", {}).get("状态") == "成功"
            and kb_search.get("检索结果", {}).get("命中数量", 0) >= 1
            and "全文索引" in kb_search.get("检索结果", {}).get("说明", ""),
            kb_search.get("检索结果", {}),
        ),
        assert_true(
            "工作流规划",
            workflow.get("工作流规划结果", {}).get("是否需要工作流") is True
            and workflow.get("工作流规划结果", {}).get("是否允许自动触发") is False,
            workflow.get("工作流规划结果", {}),
        ),
        assert_true(
            "税收工作流规划",
            tax_workflow.get("工作流规划结果", {}).get("是否需要工作流") is True
            and tax_workflow.get("工作流规划结果", {}).get("是否允许自动触发") is False,
            tax_workflow.get("工作流规划结果", {}),
        ),
        assert_true(
            "真实模型推理",
            think.get("推理结果", {}).get("状态") == "成功" and bool(think.get("答复", "").strip()),
            {
                "模型": think.get("模型路由结果", {}).get("首选模型"),
                "推理状态": think.get("推理结果", {}).get("状态"),
                "答复长度": len(think.get("答复", "")),
            },
        ),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "目标地址": BASE_URL,
        "检查结果": checks,
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
    }

    output = log_dir() / f"agent-brain-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
