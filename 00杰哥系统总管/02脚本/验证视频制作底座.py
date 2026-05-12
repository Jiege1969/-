"""
名称：验证视频制作底座.py
作用：验证 v3 视频制作系统第一阶段配置、模板、任务计划、素材候选、分镜素材匹配和主题化预演脚本是否可用。
触发方式：python 验证视频制作底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取 v3 视频制作配置，只运行本地计划脚本；不处理真实媒体、不上传、不发布。
创建/修改记录：2026-04-26 创建第一阶段视频制作底座验证脚本；2026-04-27 增加内容处理素材桥接、分镜素材匹配和主题化预演验收。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "02视频制作系统"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "视频制作验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "视频制作配置.json")
    material = load_json(root / "01配置" / "视频素材登记模板.json")
    script_template = load_json(root / "01配置" / "视频脚本模板.json")
    storyboard_template = load_json(root / "01配置" / "视频分镜模板.json")
    bridge_rules = load_json(root / "01配置" / "视频素材桥接规则.json")
    theme_rules = load_json(root / "01配置" / "视频主题化生成规则.json")
    script = root / "02脚本" / "生成视频制作计划.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    candidate_script = root / "02脚本" / "生成视频素材候选.py"
    candidate_result = subprocess.run(
        [sys.executable, str(candidate_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    match_script = root / "02脚本" / "生成视频分镜素材匹配.py"
    match_result = subprocess.run(
        [sys.executable, str(match_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    theme_script = root / "02脚本" / "生成视频主题化预演.py"
    theme_result = subprocess.run(
        [sys.executable, str(theme_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    latest_plan = root / "03数据" / "04任务计划" / "视频制作计划_最新.json"
    latest_script = root / "03数据" / "02脚本草稿" / "视频脚本草稿_最新.json"
    latest_storyboard = root / "03数据" / "03分镜计划" / "视频分镜计划_最新.json"
    latest_candidates = root / "03数据" / "05素材候选" / "视频素材候选_最新.json"
    latest_matches = root / "03数据" / "06分镜素材匹配" / "视频分镜素材匹配_最新.json"
    latest_theme = root / "03数据" / "07主题化预演" / "视频主题化预演_最新.json"
    plan_data = load_json(latest_plan) if latest_plan.exists() else {}
    draft_data = load_json(latest_script) if latest_script.exists() else {}
    storyboard_data = load_json(latest_storyboard) if latest_storyboard.exists() else {}
    candidate_data = load_json(latest_candidates) if latest_candidates.exists() else {}
    match_data = load_json(latest_matches) if latest_matches.exists() else {}
    theme_data = load_json(latest_theme) if latest_theme.exists() else {}

    checks = [
        check("视频制作配置", "默认流程" in config and "输出规则" in config, config.get("说明")),
        check("素材登记模板", "素材" in material and isinstance(material.get("素材"), list), material.get("说明")),
        check("脚本模板", "脚本结构" in script_template and "安全要求" in script_template, script_template.get("说明")),
        check("分镜模板", "镜头字段" in storyboard_template and "默认镜头" in storyboard_template, storyboard_template.get("说明")),
        check("素材桥接规则", "桥接范围" in bridge_rules and "安全边界" in bridge_rules, bridge_rules.get("来源系统")),
        check("主题化生成规则", "主题方向" in theme_rules and "封面标题规则" in theme_rules, theme_rules.get("阶段")),
        check("计划脚本执行", result.returncode == 0, (result.stdout or "").strip() or (result.stderr or "").strip()),
        check("素材候选脚本执行", candidate_result.returncode == 0, (candidate_result.stdout or "").strip() or (candidate_result.stderr or "").strip()),
        check("分镜素材匹配脚本执行", match_result.returncode == 0, (match_result.stdout or "").strip() or (match_result.stderr or "").strip()),
        check("主题化预演脚本执行", theme_result.returncode == 0, (theme_result.stdout or "").strip() or (theme_result.stderr or "").strip()),
        check("最新任务计划", latest_plan.exists(), str(latest_plan)),
        check("任务计划结构", "任务列表" in plan_data and "安全边界" in plan_data, plan_data.get("素材数量")),
        check("最新脚本草稿", latest_script.exists(), str(latest_script)),
        check("脚本草稿结构", "脚本结构" in draft_data and "安全要求" in draft_data, draft_data.get("当前状态")),
        check("最新分镜计划", latest_storyboard.exists(), str(latest_storyboard)),
        check("分镜计划结构", "镜头" in storyboard_data and "镜头字段" in storyboard_data, storyboard_data.get("当前状态")),
        check("最新素材候选", latest_candidates.exists(), str(latest_candidates)),
        check(
            "素材候选结构",
            "素材候选" in candidate_data and candidate_data.get("安全边界", {}).get("允许转码素材") is False,
            {"候选数量": candidate_data.get("候选数量"), "阻断数量": candidate_data.get("阻断数量")},
        ),
        check("最新分镜素材匹配", latest_matches.exists(), str(latest_matches)),
        check(
            "分镜素材匹配结构",
            "匹配" in match_data and match_data.get("是否调用剪辑软件") is False and match_data.get("是否转码素材") is False,
            {"匹配数量": match_data.get("匹配数量")},
        ),
        check("最新主题化预演", latest_theme.exists(), str(latest_theme)),
        check(
            "主题化预演结构",
            len(theme_data.get("主题方案", [])) >= 1
            and len(theme_data.get("字幕要点", [])) >= 1
            and len(theme_data.get("封面标题预演", [])) >= 1,
            {"主题方案数量": len(theme_data.get("主题方案", [])), "字幕要点数量": len(theme_data.get("字幕要点", []))},
        ),
        check(
            "主题化预演安全边界",
            theme_data.get("是否调用剪辑软件") is False
            and theme_data.get("是否生成真实媒体") is False
            and theme_data.get("是否上传发布") is False,
            theme_data.get("安全边界"),
        ),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "video-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"video-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "video-base-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
