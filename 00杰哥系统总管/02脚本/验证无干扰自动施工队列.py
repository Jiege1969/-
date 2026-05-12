# -*- coding: utf-8 -*-
"""
名称：验证无干扰自动施工队列.py
作用：验收无干扰自动施工规则和队列是否存在、可读、边界完整。
触发方式：python 验证无干扰自动施工队列.py
安全边界：只读配置和队列产物；只写验收报告；不重启服务；不发送企业微信；不触发 n8n；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
CONFIG = MANAGER / "01配置" / "无干扰自动施工模式规则.json"
QUEUE_JSON = MANAGER / "03数据" / "运行状态" / "无干扰自动施工队列_最新.json"
QUEUE_MD = MANAGER / "03数据" / "运行状态" / "无干扰自动施工队列_最新.md"
MASTER_DOC = ROOT / "杰哥智能化系统全盘架构说明_20260504.md"
OUT_DIR = MANAGER / "03数据" / "运行状态"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    rule = load_json(CONFIG) if CONFIG.exists() else {}
    queue = load_json(QUEUE_JSON) if QUEUE_JSON.exists() else {}
    queue_md = load_text(QUEUE_MD) if QUEUE_MD.exists() else ""
    master = load_text(MASTER_DOC) if MASTER_DOC.exists() else ""
    safety = queue.get("安全边界", {})
    stop_rules = "\n".join(rule.get("必须停下报告", []))
    queue_items = queue.get("自动施工队列", [])

    checks = [
        check(CONFIG.exists(), "无干扰规则文件存在", str(CONFIG)),
        check(QUEUE_JSON.exists() and QUEUE_MD.exists(), "无干扰队列产物存在", str(QUEUE_JSON)),
        check("每完成一个实施步骤后" in json.dumps(rule, ensure_ascii=False), "强制总架构同步规则已写入无干扰规则", ""),
        check("股票系统永远是分析系统" in json.dumps(rule, ensure_ascii=False), "只分析不交易边界已写入无干扰规则", ""),
        check("微信短文生成器 v2.1 正式接入方案" in json.dumps(queue_items, ensure_ascii=False), "队列保留微信短文生成器接入方案", ""),
        check("微信短文生成器 v2.1 影子接入" in json.dumps(queue_items, ensure_ascii=False), "队列保留微信短文生成器影子接入预演", ""),
        check("模型路由与审稿能力只读审计" in json.dumps(queue_items, ensure_ascii=False), "队列包含影子预演后的下一步只读审计", ""),
        check("扩展系统复制骨架影子检查" in json.dumps(queue_items, ensure_ascii=False), "队列包含扩展系统复制骨架影子检查", ""),
        check("后续低风险队列补充与状态观察" in json.dumps(queue_items, ensure_ascii=False), "队列包含后续低风险观察项", ""),
        check("企业微信助手统一路由状态基线" in json.dumps(queue_items, ensure_ascii=False), "队列包含企业微信助手统一路由状态基线", ""),
        check("总管小流量执行器只读门禁复核" in json.dumps(queue_items, ensure_ascii=False), "队列包含下一步小流量只读门禁复核", ""),
        check("进化系统复盘材料状态基线" in json.dumps(queue_items, ensure_ascii=False), "队列包含进化系统复盘材料状态基线", ""),
        check("知识库可追溯问答只读基线脚本缺口复核" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库只读脚本缺口复核", ""),
        check("知识库证据卡格式标准影子样板" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库证据卡格式标准影子样板", ""),
        check("知识库只读问答入口影子方案" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库只读问答入口影子方案", ""),
        check("企业微信助手知识库问答入口禁用态桥接检查" in json.dumps(queue_items, ensure_ascii=False), "队列包含企业微信助手知识库问答入口禁用态桥接检查", ""),
        check("知识库问答入口灰度门禁草案" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答入口灰度门禁草案", ""),
        check("知识库问答入口人工确认单模板" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答入口人工确认单模板", ""),
        check("知识库问答灰度样本清单影子模板" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度样本清单影子模板", ""),
        check("知识库问答灰度样本填写预检脚本" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度样本填写预检脚本", ""),
        check("知识库问答灰度回滚清单影子模板" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度回滚清单影子模板", ""),
        check("知识库问答灰度总闸门影子验收" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度总闸门影子验收", ""),
        check("知识库问答灰度材料收口包" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度材料收口包", ""),
        check("知识库问答灰度后续阻断报告" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度后续阻断报告", ""),
        check("知识库问答灰度施工暂停闸口记录" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度施工暂停闸口记录", ""),
        check("知识库问答灰度许可接收清单影子模板" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度许可接收清单影子模板", ""),
        check("知识库问答灰度许可接收清单填写预检脚本" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度许可接收清单填写预检脚本", ""),
        check("知识库问答灰度链路终态索引" in json.dumps(queue_items, ensure_ascii=False), "队列包含知识库问答灰度链路终态索引", ""),
        check("旧路径口径全局巡检" in json.dumps(queue_items, ensure_ascii=False), "队列包含旧路径口径全局巡检", ""),
        check("全局低风险施工候选刷新" in json.dumps(queue_items, ensure_ascii=False), "队列包含全局低风险施工候选刷新", ""),
        check("文档索引当前路径口径复核" in json.dumps(queue_items, ensure_ascii=False), "队列包含文档索引当前路径口径复核", ""),
        check(any(item.get("自动级别") == "必须停下报告" for item in queue_items), "队列包含必须停下报告项", ""),
        check(all(value is False for value in safety.values()), "队列安全边界均为False", json.dumps(safety, ensure_ascii=False)),
        check("重启正式股票入口 19300/19302" in stop_rules, "正式股票入口变更被列为停下报告", ""),
        check("调用券商接口" in stop_rules and "自动交易" in stop_rules, "交易类动作被列为停下报告", ""),
        check("强制施工同步规则" in master, "总架构说明仍保留强制施工同步规则", ""),
        check("不发送企业微信真实消息" in queue_md, "队列 Markdown 明确不真实发送企业微信", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "无干扰自动施工队列验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "无干扰自动施工队列验收_最新.json"
    latest_md = OUT_DIR / "无干扰自动施工队列验收_最新.md"
    lines = [
        "# 无干扰自动施工队列验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, report)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
