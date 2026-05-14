# -*- coding: utf-8 -*-
"""
名称：生成股票系统交付总包.py
作用：汇总股票主动研究系统当前交付状态、入口、验收记录、关键产物和剩余阻断点。
触发方式：python 生成股票系统交付总包.py
依赖：交付控制台、自检报告、运行固化记录、使用说明。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/144交付总包；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-system-delivery-package
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


FIXED_PUBLIC_EGRESS_IP = "43.167.210.211"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def exists(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def current_trusted_ip(root: Path) -> str:
    status = load_json(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.json", {})
    retest = load_json(root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.json", {})
    return str(
        status.get("当前需放行IP")
        or status.get("固定公网出口IP")
        or retest.get("当前需放行IP")
        or retest.get("固定公网出口IP")
        or FIXED_PUBLIC_EGRESS_IP
    )


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统交付总包 - {report['生成时间']}",
        "",
        "## 一、交付结论",
        "",
        f"- 当前交付层级：{report['当前交付层级']}",
        f"- 日常可用结论：{report['日常可用结论']}",
        f"- 剩余硬阻断：{report['剩余硬阻断']}",
        f"- 固定公网出口IP：`{report['固定公网出口IP']}`",
        "",
        "## 二、日常入口",
        "",
    ]
    for item in report["日常入口"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 三、关键产物", ""])
    for name, item in report["关键产物"].items():
        lines.append(f"- {name}：{'存在' if item['存在'] else '缺失'}，`{item['路径']}`")
    lines.extend(["", "## 四、验收记录", ""])
    for item in report["验收记录"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 五、下一步动作", ""])
    for item in report["下一步动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    trusted_ip = current_trusted_ip(root)
    self_check = load_json(root / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.json", {})
    console = load_json(root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.json", {})
    level = str(self_check.get("当前交付层级") or console.get("当前状态", {}).get("交付层级") or "未知")
    real_wecom_ok = bool(self_check.get("层级验收", {}).get("D真实灰度可用", {}).get("是否通过"))
    daily_ok = bool(
        self_check.get("层级验收", {}).get("A本地可用", {}).get("是否通过")
        and self_check.get("层级验收", {}).get("C3n8n手动受控测试", {}).get("是否通过")
    )
    records_dir = root / "03数据" / "运行固化记录"
    entry_dir = root / "05入口工具"
    record_files = [
        ("用户增强观察池", "用户增强观察池生成验收记录_20260501.md"),
        ("L8X综合样本池", "L8X综合样本池接入验收记录_20260501.md"),
        ("主动研究本地闭环", "股票主动研究本地闭环验收记录_20260501.md"),
        ("反馈与复盘", "反馈记录与轻量复盘验收记录_20260501.md"),
        ("企微灰度发送", "企微主动研究灰度发送验收记录_20260501.md"),
        ("n8n未激活导入", "n8n未激活导入验收记录_20260501.md"),
        ("n8n手动受控测试", "n8n手动受控测试验收记录_20260501.md"),
        ("交付控制台", "交付控制台验收记录_20260501.md"),
        ("日常速查卡", "股票系统日常速查卡验收记录_20260501.md"),
        ("质量观察面板", "股票系统质量观察面板验收记录_20260501.md"),
        ("质量观察历史", "股票系统质量观察历史验收记录_20260501.md"),
        ("模型健康检查", "股票系统模型健康检查验收记录_20260501.md"),
        ("金融专项复核", "股票金融专项复核验收记录_20260501.md"),
        ("报告安全边界检查", "股票系统报告安全边界检查验收记录_20260501.md"),
        ("C+++日常可用总验收", "股票系统C加加加日常可用总验收记录_20260501.md"),
        ("可信IP放行后最终验收包", "股票系统可信IP放行后最终验收包验收记录_20260501.md"),
        ("可信IP状态监测", "股票系统可信IP状态监测验收记录_20260501.md"),
        ("可信IP状态监测防旧IP加固", "股票系统可信IP状态监测防旧IP加固记录_20260501.md"),
        ("旧真实复测入口安全跳转", "股票系统旧真实复测入口安全跳转记录_20260501.md"),
        ("真实发送入口清点", "股票系统真实发送入口清点验收记录_20260501.md"),
        ("桌面AI接续材料删除", "桌面AI接续材料删除记录_20260501.md"),
        ("入口注册表同步", "股票系统入口注册表同步验收记录_20260501.md"),
        ("完整本地闭环复测", "股票系统完整本地闭环复测记录_20260501_1944.md"),
        ("企微真实推送复测控制器", "股票系统企微真实推送复测控制器验收记录_20260501.md"),
        ("完全交付最终验收", "股票系统完全交付最终验收记录_20260501.md"),
        ("可信IP放行后操作卡", "股票系统可信IP放行后操作卡记录_20260501.md"),
        ("日常一键运行", "股票系统日常一键运行验收记录_20260501.md"),
    ]
    report = {
        "名称": "股票系统交付总包",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统交付总包.py",
        "当前交付层级": level,
        "日常可用结论": ("可日常使用：本地闭环、AI报告、n8n手动受控测试、企业微信真实灰度推送均已可用。" if real_wecom_ok else "可日常使用：本地闭环、AI报告、n8n手动受控测试可用；企业微信真实主动推送待可信IP修复。") if daily_ok else "未达到日常可用，请先查看交付自检。",
        "剩余硬阻断": "企业微信应用主动消息可信IP白名单" if not real_wecom_ok else "无",
        "固定公网出口IP": trusted_ip,
        "日常入口": [
            {"名称": "日常速查卡", "路径": str(entry_dir / "股票系统日常使用速查卡_打开.bat")},
            {"名称": "质量观察面板", "路径": str(entry_dir / "股票系统质量观察面板_打开.bat")},
            {"名称": "质量观察历史", "路径": str(entry_dir / "股票系统质量观察历史_打开.bat")},
            {"名称": "模型健康检查", "路径": str(entry_dir / "股票系统模型健康检查_打开.bat")},
            {"名称": "金融专项复核", "路径": str(entry_dir / "股票系统金融专项复核_运行L5第一只.bat")},
            {"名称": "金融专项复核按代码运行", "路径": str(entry_dir / "股票系统金融专项复核_按代码运行.bat")},
            {"名称": "金融专项复核索引", "路径": str(entry_dir / "股票金融专项复核索引_打开.bat")},
            {"名称": "报告安全边界检查", "路径": str(entry_dir / "股票系统报告安全边界检查_打开.bat")},
            {"名称": "C+++日常可用总验收", "路径": str(entry_dir / "股票系统C+++日常可用总验收_打开.bat")},
            {"名称": "可信IP放行后最终验收包", "路径": str(entry_dir / "股票系统可信IP放行后最终验收包_打开.bat")},
            {"名称": "可信IP状态监测", "路径": str(entry_dir / "股票系统可信IP状态监测_打开.bat")},
            {"名称": "企微真实推送复测预检", "路径": str(entry_dir / "股票系统企微真实推送复测_预检不发送.bat")},
            {"名称": "企微真实推送复测", "路径": str(entry_dir / "股票系统企微真实推送复测_确认可信IP后真实发送.bat")},
            {"名称": "完全交付最终验收", "路径": str(entry_dir / "股票系统完全交付最终验收_打开.bat")},
            {"名称": "可信IP放行后操作卡", "路径": str(entry_dir / "股票系统可信IP放行后操作卡_打开.bat")},
            {"名称": "真实发送入口清点", "路径": str(entry_dir / "股票系统真实发送入口清点报告_打开.bat")},
            {"名称": "一键运行并查看质量面板", "路径": str(entry_dir / "股票系统一键运行并查看质量面板.bat")},
            {"名称": "快速刷新状态不跑闭环", "路径": str(entry_dir / "股票系统快速刷新状态_不跑闭环.bat")},
            {"名称": "查看状态", "路径": str(entry_dir / "股票系统交付控制台_查看状态.bat")},
            {"名称": "运行闭环", "路径": str(entry_dir / "股票系统交付控制台_运行闭环.bat")},
            {"名称": "n8n手动测试", "路径": str(entry_dir / "股票系统交付控制台_n8n手动测试.bat")},
        ],
        "关键产物": {
            "AI分析报告": exists(root / "03数据" / "135分层日报" / "AI分析报告_最新.md"),
            "企微推送草案": exists(root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"),
            "复盘报告": exists(root / "03数据" / "137复盘报告" / "股票周复盘_轻量_最新.md"),
            "交付自检": exists(root / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.md"),
            "交付控制台": exists(root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.md"),
            "企微可信IP修复包": exists(root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.md"),
            "日常速查卡": exists(root / "03数据" / "145日常速查卡" / "股票系统日常使用速查卡_最新.md"),
            "质量观察面板": exists(root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md"),
            "质量观察历史": exists(root / "03数据" / "147质量观察历史" / "股票系统质量观察历史_最新.md"),
            "模型健康检查": exists(root / "03数据" / "148模型健康检查" / "股票系统模型健康检查_最新.md"),
            "金融专项复核": exists(root / "03数据" / "149金融专项复核" / "股票金融专项复核_最新.md"),
            "金融专项复核索引": exists(root / "03数据" / "149金融专项复核索引" / "股票金融专项复核索引_最新.md"),
            "报告安全边界检查": exists(root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.md"),
            "C+++日常可用总验收": exists(root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md"),
            "可信IP放行后最终验收包": exists(root / "03数据" / "154可信IP放行后最终验收包" / "股票系统可信IP放行后最终验收包_最新.md"),
            "可信IP状态监测": exists(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.md"),
            "企微真实推送复测控制器": exists(root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.md"),
            "完全交付最终验收": exists(root / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"),
            "可信IP放行后操作卡": exists(root / "03数据" / "159可信IP放行后操作卡" / "股票系统可信IP放行后操作卡_最新.md"),
            "真实发送入口清点": exists(root / "03数据" / "160真实发送入口清点" / "股票系统真实发送入口清点报告_最新.md"),
            "日常一键运行记录": exists(root / "03数据" / "156日常一键运行" / "股票系统日常一键运行_最新.md"),
            "使用说明": exists(root / "07文档" / "股票主动研究系统本地使用说明_20260501.md"),
        },
        "验收记录": [{"名称": name, "路径": str(records_dir / filename), "存在": (records_dir / filename).exists()} for name, filename in record_files],
        "下一步动作": [
            "日常使用先运行05入口工具中的“股票系统交付控制台_查看状态”。",
            "不确定怎么操作时先打开05入口工具中的“股票系统日常使用速查卡_打开”。",
            "需要看每日质量状态时打开05入口工具中的“股票系统质量观察面板_打开”。",
            "需要看质量趋势时打开05入口工具中的“股票系统质量观察历史_打开”。",
            "需要排查模型路由时打开05入口工具中的“股票系统模型健康检查_打开”。",
            "需要对L5股票做专业金融口径复核时运行05入口工具中的“股票系统金融专项复核_运行L5第一只”。",
            "需要指定L5股票做金融复核时运行05入口工具中的“股票系统金融专项复核_按代码运行”。",
            "需要查看金融复核历史时打开05入口工具中的“股票金融专项复核索引_打开”。",
            "需要检查报告是否出现交易指令越界表述时打开05入口工具中的“股票系统报告安全边界检查_打开”。",
            "需要最终确认当前C+++日常可用形态时打开05入口工具中的“股票系统C+++日常可用总验收_打开”。",
            "企业微信后台加入可信IP前，先打开05入口工具中的“股票系统可信IP放行后最终验收包_打开”查看验收步骤。",
            "需要确认当前是否仍卡可信IP时，打开05入口工具中的“股票系统可信IP状态监测_打开”。",
            f"企业微信后台加入固定公网出口IP {trusted_ip} 前，可先运行“股票系统企微真实推送复测_预检不发送”。",
            f"企业微信后台加入固定公网出口IP {trusted_ip} 后，不确定步骤时先打开“股票系统可信IP放行后操作卡_打开”。",
            "担心真实发送入口混乱时，打开“股票系统真实发送入口清点报告_打开”。",
            f"企业微信后台加入固定公网出口IP {trusted_ip} 后，再运行“股票系统企微真实推送复测_确认可信IP后真实发送”。",
            "真实推送复测完成后，运行“股票系统完全交付最终验收_打开”确认是否进入完全交付状态。",
            "最省心的日常使用方式：运行05入口工具中的“股票系统一键运行并查看质量面板”。",
            "只想刷新状态、不重新跑AI闭环时：运行05入口工具中的“股票系统快速刷新状态_不跑闭环”。",
            "需要生成当天报告时运行“股票系统交付控制台_运行闭环”。",
            "需要复验n8n时运行“股票系统交付控制台_n8n手动测试”。",
            "旧的交付控制台真实复测入口保留可用，但优先使用新的“企微真实推送复测控制器”。",
        ],
        "安全边界": {
            "是否启用n8n": False,
            "是否自动触发n8n": False,
            "是否企业微信真实发送成功": real_wecom_ok,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    output_dir = root / "03数据" / "144交付总包"
    latest_json = output_dir / "股票系统交付总包_最新.json"
    latest_md = output_dir / "股票系统交付总包_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "当前交付层级": level,
        "日常可用": daily_ok,
        "Markdown": str(latest_md),
        "JSON": str(latest_json),
    }, ensure_ascii=False))
    return 0 if daily_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
