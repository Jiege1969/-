# -*- coding: utf-8 -*-
"""
名称：生成股票系统日常速查卡.py
作用：生成股票分析系统日常使用速查卡，并创建05入口工具打开入口。
触发方式：python 生成股票系统日常速查卡.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/145日常速查卡和05入口工具；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-system-daily-quick-card
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def mtime_text(path: Path) -> str:
    if not path.exists():
        return "未生成"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def key_files(root: Path) -> dict[str, str]:
    return {
        "交付总包": str(root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md"),
        "交付控制台": str(root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.md"),
        "AI分析报告": str(root / "03数据" / "135分层日报" / "AI分析报告_最新.md"),
        "报告可信度面板": str(root / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.md"),
        "风险失效条件观察面板": str(root / "03数据" / "184风险失效条件观察面板" / "股票风险失效条件观察面板_最新.md"),
        "公司概况补全底稿": str(root / "03数据" / "171公司概况补全底稿" / "公司概况补全底稿_最新.md"),
        "公司概况人工核验模板": str(root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.md"),
        "公司概况导入预览": str(root / "03数据" / "173公司概况导入预览" / "公司概况核验导入预览_最新.md"),
        "事件风险证据补全底稿": str(root / "03数据" / "174事件风险证据补全底稿" / "事件风险证据补全底稿_最新.md"),
        "事件风险证据人工核验模板": str(root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.md"),
        "事件风险证据核验预览": str(root / "03数据" / "176事件风险证据核验预览" / "事件风险证据核验预览_最新.md"),
        "行业景气证据补全底稿": str(root / "03数据" / "177行业景气证据补全底稿" / "行业景气证据补全底稿_最新.md"),
        "行业景气人工核验模板": str(root / "03数据" / "178行业景气人工核验模板" / "行业景气人工核验模板_最新.md"),
        "行业景气核验预览": str(root / "03数据" / "179行业景气核验预览" / "行业景气核验预览_最新.md"),
        "证据核验总览面板": str(root / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.md"),
        "证据核验导入执行闸口": str(root / "03数据" / "181证据核验导入执行闸口" / "股票证据核验导入执行闸口_最新.md"),
        "企微推送草案": str(root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"),
        "前台输出标准": str(root / "01配置" / "股票前台输出标准_v2.json"),
        "质量观察面板": str(root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md"),
        "模型健康检查": str(root / "03数据" / "148模型健康检查" / "股票系统模型健康检查_最新.md"),
        "报告安全边界": str(root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.md"),
        "C+++总验收": str(root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md"),
        "完全交付最终验收": str(root / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"),
    }


def build_markdown(report: dict[str, Any]) -> str:
    files = report["关键文件"]
    lines = [
        f"# 股票系统日常使用速查卡 - {report['生成时间']}",
        "",
        "## 一、当前能不能用",
        "",
        f"- 当前结论：{report['当前结论']}",
        f"- 当前层级：{report['当前交付层级']}",
        f"- 最近最终验收：{report['最终验收时间']}",
        "- 安全边界：不连接券商接口，不自动交易；输出只作为研究参考。",
        "",
        "## 二、企业微信里怎么问",
        "",
        "直接在【杰哥的股票分析专家】或股票助手入口里输入：",
        "",
        "- `帮助`：查看能问什么。",
        "- `今日推荐` / `今天有什么值得看`：查看今日推荐股和观察股。",
        "- `分析天齐锂业` / `分析300750`：查看单只股票的结论、策略、位置和风险。",
        "- `我持仓天齐锂业还能不能拿`：查看持仓诊断。",
        "- `股票系统状态`：查看系统是否可完整使用。",
        "- `模型健康`：查看主流程模型是否可用。",
        "- `公网状态`：查看手机外网/公网回调是否可用。",
        "",
        "前台回复原则：先给结论，再给策略、参考位置、风险观察线和下一步；技术指标和详细证据留在后台报告。",
        "",
        "## 三、本地每天怎么用",
        "",
        "1. 打开 `05入口工具\\股票系统一键运行并查看质量面板.bat`：生成当日闭环、报告和质量面板。",
        "2. 打开 `05入口工具\\股票系统快速刷新状态_不跑闭环.bat`：只刷新状态，不重跑闭环。",
        "3. 打开 `05入口工具\\股票系统质量观察面板_打开.bat`：看质量面板。",
        "4. 打开 `05入口工具\\股票系统C+++日常可用总验收_打开.bat`：做日常可用验收。",
        "5. 打开 `05入口工具\\股票系统完全交付最终验收_打开.bat`：做最终交付验收。",
        "6. 查看 `03数据\\170报告可信度面板\\股票报告可信度与数据缺口面板_最新.md`：看今日报告哪些结论证据够硬、哪些数据还缺。",
        "7. 查看 `03数据\\184风险失效条件观察面板\\股票风险失效条件观察面板_最新.md`：看每只L5股票的承接观察线、风险观察线、强度确认线和失效条件。",
        "8. 查看 `03数据\\171公司概况补全底稿\\公司概况补全底稿_最新.md`：看哪些公司概况可以优先人工核验补齐。",
        "9. 查看 `03数据\\172公司概况人工核验模板\\公司概况人工核验模板_最新.json`：按证据填写公司概况，后续再导入正式档案。",
        "10. 查看 `03数据\\173公司概况导入预览\\公司概况核验导入预览_最新.md`：看已核验内容是否满足导入条件。",
        "11. 查看 `03数据\\174事件风险证据补全底稿\\事件风险证据补全底稿_最新.md`：看公告、解禁减持、行业价格和监管诉讼等风险证据缺口。",
        "12. 查看 `03数据\\175事件风险证据人工核验模板\\事件风险证据人工核验模板_最新.json`：按官方或可信来源填写事件风险核验结果。",
        "13. 查看 `03数据\\176事件风险证据核验预览\\事件风险证据核验预览_最新.md`：只预览已核验记录，不自动改推荐。",
        "14. 查看 `03数据\\177行业景气证据补全底稿\\行业景气证据补全底稿_最新.md`：看L5股票行业景气估算与正式证据缺口。",
        "15. 查看 `03数据\\178行业景气人工核验模板\\行业景气人工核验模板_最新.json`：按行业指数、价格、官方统计或正式披露填写核验结果。",
        "16. 查看 `03数据\\179行业景气核验预览\\行业景气核验预览_最新.md`：只预览已核验记录，不自动改推荐。",
        "17. 查看 `03数据\\180证据核验总览面板\\股票证据核验总览面板_最新.md`：汇总三条证据核验链路，安排人工核验优先级。",
        "18. 查看 `03数据\\181证据核验导入执行闸口\\股票证据核验导入执行闸口_最新.md`：判断是否允许进入正式导入；默认只判断，不执行。",
        "",
        "## 四、现在不要做什么",
        "",
        "- 不把AI输出当作交易指令。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不随意恢复旧系统根目录或旧脚本入口。",
        "- 不把桌面当作长期入口目录；入口统一放在 `05入口工具`。",
        "",
        "## 五、关键文件",
        "",
    ]
    for name, path in files.items():
        lines.append(f"- {name}: `{path}`")
    lines.extend([
        "",
        "## 六、最短说明",
        "",
        "股票分析系统已经处于可交付使用状态。日常使用优先通过企业微信自然语言询问，或者通过05入口工具运行一键流程。后续优化重点是提高报告可信度、公司品质档案、复盘学习和推送体验。",
    ])
    return "\n".join(lines) + "\n"


def write_entry_open_bat(root: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统日常使用速查卡_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    final_acceptance = root / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"
    report = {
        "名称": "股票系统日常使用速查卡",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统日常速查卡.py",
        "当前交付层级": "完全交付：本地闭环 + 企业微信桥接 + 公网回调可用",
        "当前结论": "股票分析系统已可完整使用；前台支持帮助、今日推荐、单股分析、持仓诊断、系统状态、模型健康和公网状态。",
        "最终验收时间": mtime_text(final_acceptance),
        "关键文件": key_files(root),
        "安全边界": {
            "是否启用n8n自动触发": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    output_dir = root / "03数据" / "145日常速查卡"
    output_json = output_dir / f"股票系统日常使用速查卡_{stamp}.json"
    output_md = output_dir / f"股票系统日常使用速查卡_{stamp}.md"
    latest_json = output_dir / "股票系统日常使用速查卡_最新.json"
    latest_md = output_dir / "股票系统日常使用速查卡_最新.md"
    md = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, md)
    write_text(latest_md, md)
    entry_bat = write_entry_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "速查卡": str(latest_md),
        "入口工具": str(entry_bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
