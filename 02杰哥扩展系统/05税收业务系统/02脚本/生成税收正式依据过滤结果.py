"""
名称：生成税收正式依据过滤结果.py
作用：综合政策全文索引和官方来源核验结果，生成正式依据候选清单与阻断清单。
触发方式：python 生成税收正式依据过滤结果.py
依赖：Python 标准库；需先生成税收政策全文索引和政策来源核验结果。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只生成本地过滤结果，不输出最终税务结论，不替代人工判断。
创建/修改记录：2026-04-26 创建正式依据过滤脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_source_verify(root: Path) -> Path:
    latest = root / "03数据" / "06依据过滤" / "税收政策来源核验_最新.json"
    if latest.exists():
        return latest
    script = root / "02脚本" / "核验税收政策官方来源.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def build_basis_filter() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "税收官方来源核验规则.json")
    latest_policy_index = root / "03数据" / "02分类索引" / "税收政策全文索引_最新.json"
    latest_verify = ensure_source_verify(root)
    policy_index = load_json(latest_policy_index) if latest_policy_index.exists() else {}
    verify_index = load_json(latest_verify) if latest_verify.exists() else {}
    output_dir = root / "03数据" / "06依据过滤"
    output_dir.mkdir(parents=True, exist_ok=True)

    allowed_states = set(rules.get("有效状态允许值", []))
    verify_by_id = {item.get("政策ID", ""): item for item in verify_index.get("核验结果", [])}
    candidates = []
    blocked = []
    for policy in policy_index.get("政策文件", []):
        policy_id = policy.get("政策ID", "")
        verify = verify_by_id.get(policy_id, {})
        reasons = []
        if policy.get("可作为正式依据") is not True:
            reasons.append("政策全文索引未标记为可作为正式依据")
        if policy.get("有效状态") not in allowed_states:
            reasons.append(f"有效状态不合格：{policy.get('有效状态', '未标注')}")
        if verify.get("来源核验结论") != "官方来源":
            reasons.append(f"来源未通过官方核验：{verify.get('来源核验结论', '未核验')}")
        if verify.get("是否可进入正式依据候选") is not True:
            reasons.extend([item for item in verify.get("阻断原因", []) if item not in reasons])

        item = {
            "政策ID": policy_id,
            "标题": policy.get("标题", policy.get("文件名", "")),
            "文号": policy.get("文号", ""),
            "有效状态": policy.get("有效状态", "待核实"),
            "来源链接": policy.get("来源链接", ""),
            "来源核验结论": verify.get("来源核验结论", "未核验"),
            "匹配域名": verify.get("匹配域名", ""),
            "清洗文本路径": policy.get("清洗文本路径", ""),
            "分块数量": policy.get("分块数量", 0),
        }
        if not reasons:
            candidates.append(item)
        else:
            item["阻断原因"] = reasons
            blocked.append(item)

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "政策索引来源": str(latest_policy_index),
        "来源核验来源": str(latest_verify),
        "正式依据候选": candidates,
        "阻断依据": blocked,
        "统计": {
            "正式依据候选数量": len(candidates),
            "阻断数量": len(blocked),
            "总政策数量": len(candidates) + len(blocked),
        },
        "是否替代人工判断": False,
        "安全说明": "本结果只表示资料是否满足进入正式依据候选的最低条件，不能直接作为最终税务处理结论。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"税收正式依据过滤_{timestamp}.json"
    latest = output_dir / "税收正式依据过滤_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "blocked_count": len(blocked), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_basis_filter()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
