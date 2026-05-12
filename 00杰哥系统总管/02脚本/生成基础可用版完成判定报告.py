"""
名称：生成基础可用版完成判定报告.py
作用：汇总当前总体验收、核心模块验收和真实动作关闭状态，生成基础可用版完成判定报告。
触发方式：python 生成基础可用版完成判定报告.py
依赖：Python 标准库；需已有最新总体验收和各模块验收日志。
所属系统：00杰哥系统总管
安全边界：只读取日志和状态文件，只写入阶段判定报告；不接管真实业务、不触发n8n、不发送企业微信、不删除文件。
创建/修改记录：2026-04-27 创建基础可用版完成判定报告脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def latest_file(directory: Path, filename: str) -> Path | None:
    path = directory / filename
    return path if path.exists() else None


def check_latest_summary(directory_name: str, filename: str) -> dict[str, Any]:
    root = v3_root()
    path = latest_file(root / "00杰哥系统总管" / "04日志" / directory_name, filename)
    if not path:
        return {"日志目录": directory_name, "存在": False, "通过": False}
    data = load_json(path)
    summary = data.get("汇总", {})
    passed = summary.get("失败") == 0 or summary.get("failed") == 0
    return {
        "日志目录": directory_name,
        "日志文件": str(path),
        "存在": True,
        "通过": passed,
        "汇总": summary,
    }


def check_false_flags(path: Path, flags: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {"文件": str(path), "存在": False, "通过": False}
    data = load_json(path)
    values = {flag: data.get(flag) for flag in flags}
    return {
        "文件": str(path),
        "存在": True,
        "通过": all(value is False for value in values.values()),
        "检查值": values,
    }


def build_report() -> dict[str, Any]:
    root = v3_root()
    acceptance_path = latest_file(root / "00杰哥系统总管" / "04日志" / "acceptance", "v3-acceptance-最新.json")
    acceptance = load_json(acceptance_path) if acceptance_path else {}
    acceptance_summary = acceptance.get("summary", {})
    acceptance_steps = acceptance.get("steps", [])
    module_checks = [
        check_latest_summary("知识库验收", "knowledge-base-verify-最新.json"),
        check_latest_summary("知识库验收", "knowledge-retrieval-enhancement-chain-verify-最新.json"),
        check_latest_summary("知识库入库前复核", "knowledge-local-ingest-review-verify-最新.json"),
        check_latest_summary("知识库入库前复核", "knowledge-write-disabled-verify-最新.json"),
        check_latest_summary("知识库入库前复核", "r02-knowledge-local-ingest-executor-verify-最新.json"),
        check_latest_summary("进化系统验收", "evolution-base-verify-最新.json"),
        check_latest_summary("工作流验收", "workflow-base-verify-最新.json"),
        check_latest_summary("n8n导入审查验收", "n8n-import-review-verify-最新.json"),
        check_latest_summary("工作流验收", "first-batch-n8n-disabled-workflow-draft-verify-最新.json"),
        check_latest_summary("灰度接入验收", "low-risk-gray-access-verify-最新.json"),
        check_latest_summary("灰度接入验收", "first-batch-n8n-controlled-verify-最新.json"),
        check_latest_summary("日常可用版", "daily-usable-entry-verify-最新.json"),
        check_latest_summary("日常可用版", "daily-task-entry-queue-verify-最新.json"),
        check_latest_summary("日常可用版", "daily-task-confirmation-verify-最新.json"),
        check_latest_summary("日常可用版", "daily-task-release-plan-verify-最新.json"),
        check_latest_summary("日常可用版", "daily-usable-stage-report-verify-最新.json"),
        check_latest_summary("稳定中台", "stable-hub-heartbeat-verify-最新.json"),
        check_latest_summary("稳定中台", "stable-hub-diagnosis-plan-verify-最新.json"),
        check_latest_summary("稳定中台", "stable-hub-patrol-verify-最新.json"),
        check_latest_summary("无人值守守护", "unattended-guardian-permission-tier-verify-最新.json"),
        check_latest_summary("无人值守守护", "unattended-task-state-machine-verify-最新.json"),
        check_latest_summary("无人值守守护", "unattended-task-queue-seed-verify-最新.json"),
        check_latest_summary("模型资源池", "model-resource-pool-register-verify-最新.json"),
        check_latest_summary("智能决策内核", "manager-decision-core-register-verify-最新.json"),
        check_latest_summary("智能决策内核", "decision-sample-simulation-verify-最新.json"),
        check_latest_summary("真实接入闸门", "real-access-master-gate-verify-最新.json"),
        check_latest_summary("真实攻坚队列", "real-assault-candidate-queue-verify-最新.json"),
        check_latest_summary("真实攻坚队列", "assault-gate-completion-verify-最新.json"),
        check_latest_summary("真实攻坚队列", "readonly-disabled-completion-verify-最新.json"),
        check_latest_summary("小流量只读执行", "readonly-execution-plan-verify-最新.json"),
        check_latest_summary("小流量只读执行", "readonly-pre-execution-snapshot-verify-最新.json"),
        check_latest_summary("小流量只读执行", "readonly-post-observation-template-verify-最新.json"),
        check_latest_summary("小流量只读执行", "readonly-rollback-template-verify-最新.json"),
        check_latest_summary("小流量只读执行", "readonly-observation-loop-verify-最新.json"),
        check_latest_summary("小流量只读执行", "readonly-batch-release-form-verify-最新.json"),
        check_latest_summary("小流量只读执行", "readonly-execution-design-stage-verify-最新.json"),
        check_latest_summary("小流量只读执行", "r01-stock-readonly-preflight-verify-最新.json"),
        check_latest_summary("小流量只读执行", "r02-knowledge-ingest-preflight-verify-最新.json"),
        check_latest_summary("小流量只读执行", "r03-office-draft-preflight-verify-最新.json"),
        check_latest_summary("小流量只读执行", "first-readonly-batch-preflight-verify-最新.json"),
        check_latest_summary("小流量只读执行", "real-readonly-final-gate-verify-最新.json"),
        check_latest_summary("小流量只读执行", "real-execution-window-register-verify-最新.json"),
        check_latest_summary("小流量只读执行", "real-execution-permit-order-verify-最新.json"),
        check_latest_summary("小流量只读执行", "first-batch-dry-run-record-verify-最新.json"),
        check_latest_summary("小流量只读执行", "first-batch-executor-readiness-table-verify-最新.json"),
        check_latest_summary("小流量只读执行", "first-batch-scheduler-adapter-table-verify-最新.json"),
        check_latest_summary("阶段判定", "current-progress-report-verify-最新.json"),
        check_latest_summary("阶段判定", "daily-usable-assault-status-report-verify-最新.json"),
        check_latest_summary("统一消息出口验收", "message-outlet-verify-最新.json"),
        check_latest_summary("OpenClaw验收", "openclaw-gateway-verify-最新.json"),
        check_latest_summary("股票研究验收", "stock-base-verify-最新.json"),
        check_latest_summary("股票公开数据探测", "stock-public-readonly-probe-verify-最新.json"),
        check_latest_summary("股票公开数据探测", "stock-url-whitelist-confirmation-verify-最新.json"),
        check_latest_summary("股票公开数据探测", "stock-readonly-request-disabled-verify-最新.json"),
        check_latest_summary("股票公开数据探测", "r01-stock-readonly-executor-verify-最新.json"),
        check_latest_summary("视频制作验收", "video-base-verify-最新.json"),
        check_latest_summary("视频素材门禁", "video-local-material-gate-verify-最新.json"),
        check_latest_summary("视频素材门禁", "video-render-disabled-verify-最新.json"),
        check_latest_summary("本职工作验收", "work-base-verify-最新.json"),
        check_latest_summary("办公材料门禁", "office-local-draft-gate-verify-最新.json"),
        check_latest_summary("办公材料门禁", "office-final-output-disabled-verify-最新.json"),
        check_latest_summary("办公材料门禁", "r03-office-draft-executor-verify-最新.json"),
        check_latest_summary("内容处理验收", "content-processing-base-verify-最新.json"),
        check_latest_summary("内容处理门禁", "content-local-convert-gate-verify-最新.json"),
        check_latest_summary("内容处理门禁", "content-real-convert-disabled-verify-最新.json"),
        check_latest_summary("企业微信助手验收", "wework-assistant-base-verify-最新.json"),
        check_latest_summary("企业微信沙箱门禁", "wework-sandbox-loop-gate-verify-最新.json"),
        check_latest_summary("企业微信沙箱门禁", "wework-real-send-disabled-verify-最新.json"),
    ]
    safety_checks = [
        check_false_flags(
            root / "01杰哥智能系统" / "03数据" / "工作流导入审查" / "n8n非税收导入演练清单_最新.json",
            ["是否执行导入", "是否启用Webhook", "是否触发真实工作流", "是否包含税收业务"],
        ),
        check_false_flags(
            root / "02杰哥扩展系统" / "06企业微信助手系统" / "03数据" / "05回滚演练" / "企业微信沙盒回滚演练_最新.json",
            ["是否连接企业微信", "是否停用真实n8n工作流", "是否修改OpenClaw", "是否删除日志", "是否真实执行"],
        ),
        check_false_flags(
            root / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "07主题化预演" / "视频主题化预演_最新.json",
            ["是否调用剪辑软件", "是否生成真实媒体", "是否上传发布"],
        ),
        check_false_flags(
            root / "00杰哥系统总管" / "03数据" / "灰度接入" / "低风险灰度接入设计_最新.json",
            ["是否导入n8n", "是否启用Webhook", "是否触发真实工作流", "是否发送企业微信", "是否接入税收业务"],
        ),
        check_false_flags(
            root / "00杰哥系统总管" / "03数据" / "灰度接入" / "低风险灰度演练包_最新.json",
            ["是否导入n8n", "是否启用Webhook", "是否触发真实工作流", "是否发送企业微信", "是否接入税收业务"],
        ),
        check_false_flags(
            root / "00杰哥系统总管" / "03数据" / "灰度接入" / "低风险灰度演练结果汇总_最新.json",
            ["是否允许自动进入第2层", "是否导入n8n", "是否启用Webhook", "是否触发真实工作流", "是否发送企业微信", "是否接入税收业务"],
        ),
        check_false_flags(
            root / "00杰哥系统总管" / "03数据" / "灰度接入" / "系统状态巡检未激活导入准备包_最新.json",
            ["是否允许自动进入第2层", "是否输出真实导入命令", "是否调用n8nAPI", "是否导入n8n", "是否启用Webhook", "是否触发真实工作流", "是否发送企业微信", "是否接入税收业务"],
        ),
        check_false_flags(
            root / "00杰哥系统总管" / "03数据" / "灰度接入" / "n8n真实环境只读探测_最新.json",
            ["是否读取工作流", "是否读取凭据", "是否调用n8n写接口", "是否导入n8n", "是否启用Webhook", "是否触发真实工作流"],
        ),
    ]
    gray_log_dir = root / "00杰哥系统总管" / "04日志" / "灰度接入验收"
    inactive_import_latest = gray_log_dir / "n8n-inactive-import-execute-最新.json"
    manual_execute_latest = gray_log_dir / "n8n-local-manual-execute-最新.json"
    rollback_latest = gray_log_dir / "n8n-inactive-import-rollback-最新.json"
    kb_import_latest = gray_log_dir / "n8n-kb-inactive-import-execute-最新.json"
    kb_manual_latest = gray_log_dir / "n8n-kb-local-manual-execute-最新.json"
    kb_rollback_latest = gray_log_dir / "n8n-kb-inactive-import-rollback-最新.json"
    office_import_latest = gray_log_dir / "n8n-office-inactive-import-execute-最新.json"
    office_manual_latest = gray_log_dir / "n8n-office-local-manual-execute-最新.json"
    office_rollback_latest = gray_log_dir / "n8n-office-inactive-import-rollback-最新.json"
    video_import_latest = gray_log_dir / "n8n-video-inactive-import-execute-最新.json"
    video_manual_latest = gray_log_dir / "n8n-video-local-manual-execute-最新.json"
    video_rollback_latest = gray_log_dir / "n8n-video-inactive-import-rollback-最新.json"
    gray_real_chain = {
        "系统状态巡检未激活导入报告": str(inactive_import_latest) if inactive_import_latest.exists() else "",
        "系统状态巡检本地手动测试报告": str(manual_execute_latest) if manual_execute_latest.exists() else "",
        "系统状态巡检回滚预演报告": str(rollback_latest) if rollback_latest.exists() else "",
        "系统状态巡检已导入": inactive_import_latest.exists(),
        "系统状态巡检本地手动测试通过": manual_execute_latest.exists(),
        "系统状态巡检回滚预演通过": rollback_latest.exists(),
        "知识库问答增强未激活导入报告": str(kb_import_latest) if kb_import_latest.exists() else "",
        "知识库问答增强本地手动测试报告": str(kb_manual_latest) if kb_manual_latest.exists() else "",
        "知识库问答增强回滚预演报告": str(kb_rollback_latest) if kb_rollback_latest.exists() else "",
        "知识库问答增强已导入": kb_import_latest.exists(),
        "知识库问答增强本地手动测试通过": kb_manual_latest.exists(),
        "知识库问答增强回滚预演通过": kb_rollback_latest.exists(),
        "办公材料生成未激活导入报告": str(office_import_latest) if office_import_latest.exists() else "",
        "办公材料生成本地手动测试报告": str(office_manual_latest) if office_manual_latest.exists() else "",
        "办公材料生成回滚预演报告": str(office_rollback_latest) if office_rollback_latest.exists() else "",
        "办公材料生成已导入": office_import_latest.exists(),
        "办公材料生成本地手动测试通过": office_manual_latest.exists(),
        "办公材料生成回滚预演通过": office_rollback_latest.exists(),
        "视频素材处理未激活导入报告": str(video_import_latest) if video_import_latest.exists() else "",
        "视频素材处理本地手动测试报告": str(video_manual_latest) if video_manual_latest.exists() else "",
        "视频素材处理回滚预演报告": str(video_rollback_latest) if video_rollback_latest.exists() else "",
        "视频素材处理已导入": video_import_latest.exists(),
        "视频素材处理本地手动测试通过": video_manual_latest.exists(),
        "视频素材处理回滚预演通过": video_rollback_latest.exists(),
    }
    total_acceptance_ok = acceptance_summary.get("failed") == 0 and acceptance_summary.get("passed") == acceptance_summary.get("total")
    no_tax_step = all("tax" not in step.get("name", "").lower() and "税收" not in step.get("name", "") for step in acceptance_steps)
    module_ok = all(item.get("通过") is True for item in module_checks)
    safety_ok = all(item.get("通过") is True for item in safety_checks)
    completed = total_acceptance_ok and no_tax_step and module_ok and safety_ok
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "基础可用版完成判定",
        "范围": "非税收施工范围；税收业务按用户要求暂停",
        "总体验收": {
            "日志文件": str(acceptance_path) if acceptance_path else "",
            "通过": total_acceptance_ok,
            "汇总": acceptance_summary,
            "执行步骤数量": len(acceptance_steps),
            "是否跳过税收执行链": no_tax_step,
        },
        "模块验收": module_checks,
        "真实动作关闭状态": safety_checks,
        "完成判定": "基础可用版已完成，可进入真实接入前讨论" if completed else "基础可用版未完成",
        "阶段性工作进度百分比": 100 if completed else 90,
        "总体进度估算百分比": 99 if completed else 68,
        "真实灰度链路": gray_real_chain,
        "下一步建议": [
            "汇总第一批低风险n8n真实未激活导入结果，准备进入真实启用前风险评审",
            "保持Webhook、企业微信真实发送和税收业务接入关闭",
            "每个真实导入工作流必须完成导入、手动测试、回滚预演、总体验收四步闭环",
            "税收业务继续保持暂停，不纳入下一轮施工",
        ],
    }
    return report


def main() -> int:
    report = build_report()
    output_dir = v3_root() / "00杰哥系统总管" / "03数据" / "阶段判定"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "基础可用版完成判定_最新.json"
    latest = output_dir / "基础可用版完成判定_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"完成判定": report["完成判定"], "阶段性工作进度百分比": report["阶段性工作进度百分比"], "输出": str(output)}, ensure_ascii=True))
    return 0 if report["完成判定"].startswith("基础可用版已完成") else 1


if __name__ == "__main__":
    raise SystemExit(main())

