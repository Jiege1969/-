"""
名称：验证企业微信助手底座.py
作用：验证企业微信助手系统配置、凭据隔离、凭据路径模板、只读回环、n8n草案、联动预演、统一消息出口和回滚方案是否满足真实接入前安全底座要求。
触发方式：python 验证企业微信助手底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只运行企业微信助手本地脚本；不读取真实凭据、不连接企业微信、不触发n8n、不写统一消息出口正式队列。
创建/修改记录：2026-04-27 创建企业微信助手底座验收脚本；增加n8n工作流草案、端到端联动预演、凭据路径模板和沙盒回滚演练验收。
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
    return v3_root() / "02杰哥扩展系统" / "06企业微信助手系统"


def public_component_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "00公共组件"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "企业微信助手验收"
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


def run_script(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def main() -> int:
    root = module_root()
    public_root = public_component_root()
    config = load_json(root / "01配置" / "企业微信助手配置.json")
    credential_rules = load_json(root / "01配置" / "企业微信凭据隔离规则.json")
    credential_path_rules = load_json(root / "01配置" / "企业微信凭据路径模板.json")
    readonly_rules = load_json(root / "01配置" / "企业微信只读接入测试规则.json")
    rollback = load_json(root / "01配置" / "企业微信回滚方案.json")
    link_rules = load_json(root / "01配置" / "企业微信n8n联动规则.json")
    switches = config.get("接入开关", {})

    checklist_script = root / "02脚本" / "生成企业微信接入检查清单.py"
    credential_script = root / "02脚本" / "检查企业微信凭据隔离.py"
    credential_path_script = root / "02脚本" / "检查企业微信凭据路径模板.py"
    loopback_script = root / "02脚本" / "企业微信只读回环预演.py"
    workflow_script = root / "02脚本" / "生成企业微信n8n工作流草案.py"
    link_preview_script = root / "02脚本" / "生成企业微信联动预演.py"
    rollback_rehearsal_script = root / "02脚本" / "生成企业微信沙盒回滚演练.py"
    checklist_result = run_script(checklist_script)
    credential_result = run_script(credential_script)
    credential_path_result = run_script(credential_path_script)
    loopback_result = run_script(loopback_script)
    workflow_result = run_script(workflow_script)
    link_preview_result = run_script(link_preview_script)
    rollback_rehearsal_result = run_script(rollback_rehearsal_script)

    latest_checklist = root / "03数据" / "01接入检查" / "企业微信接入检查清单_最新.json"
    latest_credential = root / "03数据" / "01接入检查" / "企业微信凭据隔离检查_最新.json"
    latest_credential_path = root / "03数据" / "01接入检查" / "企业微信凭据路径检查_最新.json"
    latest_loopback = root / "03数据" / "02回环预演" / "企业微信只读回环预演_最新.json"
    latest_workflow = root / "03数据" / "03工作流草案" / "企业微信n8n工作流草案_最新.json"
    latest_link_preview = root / "03数据" / "04联动预演" / "企业微信联动预演_最新.json"
    latest_rollback_rehearsal = root / "03数据" / "05回滚演练" / "企业微信沙盒回滚演练_最新.json"
    checklist = load_json(latest_checklist) if latest_checklist.exists() else {}
    credential = load_json(latest_credential) if latest_credential.exists() else {}
    credential_path = load_json(latest_credential_path) if latest_credential_path.exists() else {}
    loopback = load_json(latest_loopback) if latest_loopback.exists() else {}
    workflow = load_json(latest_workflow) if latest_workflow.exists() else {}
    link_preview = load_json(latest_link_preview) if latest_link_preview.exists() else {}
    rollback_rehearsal = load_json(latest_rollback_rehearsal) if latest_rollback_rehearsal.exists() else {}
    outlet_config = public_root / "01配置" / "统一消息出口配置.json"
    openclaw_contract = public_root / "01配置" / "OpenClaw边缘网关契约.json"

    checks = [
        check("企业微信助手配置", "接入开关" in config and "消息边界" in config, config.get("阶段")),
        check("凭据隔离规则", "环境变量占位" in credential_rules and "禁止关键词" in credential_rules, list(credential_rules.get("环境变量占位", {}).keys())),
        check("凭据路径模板", "环境变量占位" in credential_path_rules and "当前开关" in credential_path_rules, list(credential_path_rules.get("环境变量占位", {}).keys())),
        check("只读接入测试规则", "预演要求" in readonly_rules and "验收标准" in readonly_rules, readonly_rules.get("测试模式")),
        check("回滚方案", len(rollback.get("回滚动作清单", [])) >= 3 and "人工确认要求" in rollback, rollback.get("回滚动作清单", [])),
        check("n8n联动规则", "n8n草案节点" in link_rules and "字段映射" in link_rules, link_rules.get("联动链路")),
        check("真实凭据读取关闭", switches.get("允许读取真实凭据") is False, switches),
        check("企业微信真实连接关闭", switches.get("允许连接企业微信") is False, switches),
        check("企业微信真实发送关闭", switches.get("允许发送企业微信") is False, switches),
        check("n8n真实触发关闭", switches.get("允许触发n8n真实工作流") is False, switches),
        check("统一消息出口配置存在", outlet_config.exists(), str(outlet_config)),
        check("OpenClaw边缘网关契约存在", openclaw_contract.exists(), str(openclaw_contract)),
        check("接入检查清单脚本执行", checklist_result.returncode == 0, (checklist_result.stdout or "").strip() or (checklist_result.stderr or "").strip()),
        check("凭据隔离检查脚本执行", credential_result.returncode == 0, (credential_result.stdout or "").strip() or (credential_result.stderr or "").strip()),
        check("凭据路径检查脚本执行", credential_path_result.returncode == 0, (credential_path_result.stdout or "").strip() or (credential_path_result.stderr or "").strip()),
        check("只读回环预演脚本执行", loopback_result.returncode == 0, (loopback_result.stdout or "").strip() or (loopback_result.stderr or "").strip()),
        check("n8n工作流草案脚本执行", workflow_result.returncode == 0, (workflow_result.stdout or "").strip() or (workflow_result.stderr or "").strip()),
        check("企业微信联动预演脚本执行", link_preview_result.returncode == 0, (link_preview_result.stdout or "").strip() or (link_preview_result.stderr or "").strip()),
        check("沙盒回滚演练脚本执行", rollback_rehearsal_result.returncode == 0, (rollback_rehearsal_result.stdout or "").strip() or (rollback_rehearsal_result.stderr or "").strip()),
        check("接入检查清单结构", checklist.get("汇总", {}).get("失败数量") == 0 and checklist.get("是否允许真实接入") is False, checklist.get("汇总")),
        check("凭据高风险检查", credential.get("高风险发现数量") == 0 and credential.get("是否发现明文凭据风险") is False, {"扫描文件数": credential.get("扫描文件数"), "高风险": credential.get("高风险发现数量")}),
        check(
            "凭据路径检查结构",
            credential_path.get("是否通过") is True
            and credential_path.get("是否读取真实凭据") is False
            and credential_path.get("是否连接企业微信") is False,
            {"占位变量数量": credential_path.get("占位变量数量"), "风险关键词命中": credential_path.get("风险关键词命中")},
        ),
        check("只读回环预演结构", loopback.get("是否通过回环预演") is True and loopback.get("边界状态", {}).get("真实发送企业微信") is False, loopback.get("边界状态")),
        check("n8n工作流草案结构", workflow.get("是否导入n8n") is False and workflow.get("是否启用Webhook") is False and workflow.get("节点数量", 0) >= 3, {"节点数量": workflow.get("节点数量")}),
        check(
            "企业微信联动预演结构",
            link_preview.get("是否导入n8n") is False
            and link_preview.get("是否连接企业微信") is False
            and link_preview.get("是否写入统一消息出口正式队列") is False
            and link_preview.get("是否真实发送") is False,
            {
                "工作流节点数量": link_preview.get("工作流节点数量"),
                "是否真实发送": link_preview.get("是否真实发送"),
            },
        ),
        check(
            "沙盒回滚演练结构",
            rollback_rehearsal.get("是否真实执行") is False
            and rollback_rehearsal.get("是否连接企业微信") is False
            and rollback_rehearsal.get("是否停用真实n8n工作流") is False
            and rollback_rehearsal.get("统计", {}).get("动作数量", 0) >= 3,
            rollback_rehearsal.get("统计"),
        ),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "wework-assistant-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"wework-assistant-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
