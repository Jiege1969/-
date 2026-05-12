"""
名称：生成税收政策案例索引.py
作用：扫描税收业务系统的政策文件目录和业务案例目录，生成只读索引清单。
触发方式：python 生成税收政策案例索引.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读取本模块政策文件和业务案例目录，只写入本模块分类索引；不抓取政策、不读取真实涉税资料、不替代正式判断。
创建/修改记录：2026-04-26 创建第一阶段税收政策案例索引脚本；排除元数据伴随文件。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_path_for(path: Path) -> Path:
    return path.with_name(f"{path.name}.元数据.json")


def scan_dir(root: Path, allowed_suffixes: set[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not root.exists():
        return items
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".元数据.json"):
            continue
        if path.suffix.lower() not in allowed_suffixes:
            continue
        stat = path.stat()
        metadata_path = metadata_path_for(path)
        items.append(
            {
                "文件名": path.name,
                "路径": str(path),
                "扩展名": path.suffix.lower(),
                "大小字节": stat.st_size,
                "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "sha256": sha256(path),
                "元数据文件": str(metadata_path),
                "登记状态": "已登记元数据" if metadata_path.exists() else "待补充元数据",
            }
        )
    return items


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "税收政策入库规则.json")
    allowed = {item.lower() for item in rules.get("允许文件类型", [])}
    policy_dir = root / "03数据" / "01政策文件"
    case_dir = root / "03数据" / "03业务案例"
    output_dir = root / "03数据" / "02分类索引"
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "政策文件目录": str(policy_dir),
        "业务案例目录": str(case_dir),
        "允许文件类型": sorted(allowed),
        "政策文件": scan_dir(policy_dir, allowed),
        "业务案例": scan_dir(case_dir, allowed),
    }
    report["政策文件数量"] = len(report["政策文件"])
    report["业务案例数量"] = len(report["业务案例"])

    output = output_dir / f"税收政策案例索引_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    latest = output_dir / "税收政策案例索引_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"政策文件数量": report["政策文件数量"], "业务案例数量": report["业务案例数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
