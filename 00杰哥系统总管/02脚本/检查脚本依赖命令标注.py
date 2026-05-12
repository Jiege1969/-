"""
名称：检查脚本依赖命令标注.py
作用：检查 v3 新系统内脚本、依赖清单、命令配置类文件是否具备自解释标注。
触发方式：python 检查脚本依赖命令标注.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取 v3 目录内文件，只在 v3 日志目录写入检查报告。
创建/修改记录：2026-04-26 创建第一版规范检查脚本；排除 03数据 下的生成数据文件。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


目标扩展名 = {".ps1", ".py", ".txt", ".yml", ".yaml", ".env"}
排除目录关键词 = {".venv", "历史经验", "03数据", "04日志", "05备份", "06临时"}
必备字段组 = {
    "名称": ("Name:", "名称："),
    "作用": ("Purpose:", "Role:", "作用："),
    "触发方式": ("Trigger:", "触发方式："),
    "依赖": ("Dependency:", "Dependencies:", "依赖："),
    "所属系统": ("System:", "Owner system:", "所属系统："),
}


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def 报告目录() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "规范检查"
    target.mkdir(parents=True, exist_ok=True)
    return target


def 是否排除(path: Path) -> bool:
    return any(part in 排除目录关键词 for part in path.parts)


def 扫描文件() -> list[Path]:
    root = v3_root()
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if 是否排除(path):
            continue
        if path.suffix.lower() in 目标扩展名:
            files.append(path)
    return sorted(files, key=lambda item: str(item))


def 检查文件(path: Path) -> dict[str, object]:
    try:
        header = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:25])
    except Exception as exc:
        return {"文件": str(path), "结果": "失败", "缺失字段": ["无法读取"], "错误": str(exc)}

    missing = []
    for name, candidates in 必备字段组.items():
        if not any(candidate in header for candidate in candidates):
            missing.append(name)

    return {
        "文件": str(path),
        "结果": "通过" if not missing else "失败",
        "缺失字段": missing,
    }


def main() -> int:
    results = [检查文件(path) for path in 扫描文件()]
    report = {
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "脚本依赖命令文件自解释标注",
        "汇总": {
            "文件数": len(results),
            "通过": sum(1 for item in results if item["结果"] == "通过"),
            "失败": sum(1 for item in results if item["结果"] != "通过"),
        },
        "结果": results,
    }
    output = 报告目录() / "annotation-check-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
