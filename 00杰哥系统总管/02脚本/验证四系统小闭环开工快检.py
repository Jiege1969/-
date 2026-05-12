# -*- coding: utf-8 -*-
"""
名称：验证四系统小闭环开工快检.py
作用：验证四系统小闭环开工快检报告是否生成且安全边界有效。
触发方式：手动验收或开工快检后由施工者本地执行。
依赖：03数据/四系统小闭环/四系统小闭环开工快检_最新.json；191最小行动卡、191资料来源导航卡、199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205候选采用确认回执草案、210确认回执状态面板、211回执后调度清单、212确认回执填写样例副本、213确认后路径演练报告、214正式回执待办卡、215正式回执填写前自检、216正式回执录入后受控重跑预演、206候选采用前闸口、198填写质量闸口、197完成后预演检查、194模板同步执行、文稿质检旁路观察与样本复盘关键文件检查项。
所属系统：00杰哥系统总管。
输出：控制台JSON验收结果。
安全边界：只读开工快检报告；不触发n8n、不发送企业微信、不写正式业务库、不更新接续包。
标识：四系统小闭环；开工快检验收；只读验证。
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
REPORT = ROOT / "00杰哥系统总管" / "03数据" / "四系统小闭环" / "四系统小闭环开工快检_最新.json"


def main() -> int:
    checks: list[dict[str, object]] = [{"名称": "开工快检报告存在", "通过": REPORT.exists()}]
    if REPORT.exists():
        data = json.loads(REPORT.read_text(encoding="utf-8-sig"))
        checks.append({"名称": "快检无失败项", "通过": data.get("失败数量") == 0})
        checks.append({"名称": "包含19300检查", "通过": any(item.get("名称") == "股票助手19300监听" for item in data.get("检查项", []))})
        checks.append({"名称": "包含19302检查", "通过": any(item.get("名称") == "企微桥接19302监听" for item in data.get("检查项", []))})
        checks.append({"名称": "包含股票5/5检查", "通过": any(item.get("名称") == "股票完全交付仍5/5" for item in data.get("检查项", []))})
        checks.append({"名称": "包含C+++日常可用验收检查", "通过": any(item.get("名称") == "股票C+++日常可用验收仍通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含四系统8/8检查", "通过": any(item.get("名称") == "四系统小闭环仍8/8" for item in data.get("检查项", []))})
        checks.append({"名称": "包含股票四系统融合检查", "通过": any(item.get("名称") == "股票四系统融合面板通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含主线脚本标头审计检查", "通过": any(item.get("名称") == "主线脚本标头审计通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含191最小行动卡验证通过检查", "通过": any(item.get("名称") == "191最小行动卡验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含191最小行动卡关键文件检查", "通过": any(item.get("名称") == "关键文件存在：191最小行动卡" for item in data.get("检查项", []))})
        checks.append({"名称": "包含191最小行动卡验证日志检查", "通过": any(item.get("名称") == "关键文件存在：191最小行动卡验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含191资料来源导航卡验证通过检查", "通过": any(item.get("名称") == "191资料来源导航卡验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含191资料来源导航卡关键文件检查", "通过": any(item.get("名称") == "关键文件存在：191资料来源导航卡" for item in data.get("检查项", []))})
        checks.append({"名称": "包含191资料来源导航卡验证日志检查", "通过": any(item.get("名称") == "关键文件存在：191资料来源导航卡验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含199资料候选处理包验证通过检查", "通过": any(item.get("名称") == "199资料候选处理包验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含199资料候选处理包关键文件检查", "通过": any(item.get("名称") == "关键文件存在：199资料候选处理包" for item in data.get("检查项", []))})
        checks.append({"名称": "包含199资料候选处理包验证日志检查", "通过": any(item.get("名称") == "关键文件存在：199资料候选处理包验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含200填写建议草案验证通过检查", "通过": any(item.get("名称") == "200填写建议草案验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含200填写建议草案关键文件检查", "通过": any(item.get("名称") == "关键文件存在：200填写建议草案" for item in data.get("检查项", []))})
        checks.append({"名称": "包含200填写建议草案验证日志检查", "通过": any(item.get("名称") == "关键文件存在：200填写建议草案验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含201最小人工确认清单验证通过检查", "通过": any(item.get("名称") == "201最小人工确认清单验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含201最小人工确认清单关键文件检查", "通过": any(item.get("名称") == "关键文件存在：201最小人工确认清单" for item in data.get("检查项", []))})
        checks.append({"名称": "包含201最小人工确认清单验证日志检查", "通过": any(item.get("名称") == "关键文件存在：201最小人工确认清单验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含202候选填写CSV副本验证通过检查", "通过": any(item.get("名称") == "202候选填写CSV副本验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含202候选填写CSV副本关键文件检查", "通过": any(item.get("名称") == "关键文件存在：202候选填写CSV副本" for item in data.get("检查项", []))})
        checks.append({"名称": "包含202候选填写CSV副本验证日志检查", "通过": any(item.get("名称") == "关键文件存在：202候选填写CSV副本验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含203候选写入差异预览验证通过检查", "通过": any(item.get("名称") == "203候选写入差异预览验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含203候选写入差异预览关键文件检查", "通过": any(item.get("名称") == "关键文件存在：203候选写入差异预览" for item in data.get("检查项", []))})
        checks.append({"名称": "包含203候选写入差异预览验证日志检查", "通过": any(item.get("名称") == "关键文件存在：203候选写入差异预览验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含204候选采用后质量预演验证通过检查", "通过": any(item.get("名称") == "204候选采用后质量预演验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含204候选采用后质量预演关键文件检查", "通过": any(item.get("名称") == "关键文件存在：204候选采用后质量预演" for item in data.get("检查项", []))})
        checks.append({"名称": "包含204候选采用后质量预演验证日志检查", "通过": any(item.get("名称") == "关键文件存在：204候选采用后质量预演验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含205候选采用确认回执草案验证通过检查", "通过": any(item.get("名称") == "205候选采用确认回执草案验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含205候选采用确认回执草案关键文件检查", "通过": any(item.get("名称") == "关键文件存在：205候选采用确认回执草案" for item in data.get("检查项", []))})
        checks.append({"名称": "包含205候选采用确认回执草案验证日志检查", "通过": any(item.get("名称") == "关键文件存在：205候选采用确认回执草案验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含210确认回执状态面板验证通过检查", "通过": any(item.get("名称") == "210确认回执状态面板验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含210确认回执状态面板关键文件检查", "通过": any(item.get("名称") == "关键文件存在：210确认回执状态面板" for item in data.get("检查项", []))})
        checks.append({"名称": "包含210确认回执状态面板验证日志检查", "通过": any(item.get("名称") == "关键文件存在：210确认回执状态面板验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含211回执后调度清单验证通过检查", "通过": any(item.get("名称") == "211回执后调度清单验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含211回执后调度清单关键文件检查", "通过": any(item.get("名称") == "关键文件存在：211回执后调度清单" for item in data.get("检查项", []))})
        checks.append({"名称": "包含211回执后调度清单验证日志检查", "通过": any(item.get("名称") == "关键文件存在：211回执后调度清单验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含212确认回执填写样例副本验证通过检查", "通过": any(item.get("名称") == "212确认回执填写样例副本验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含212确认回执填写样例副本关键文件检查", "通过": any(item.get("名称") == "关键文件存在：212确认回执填写样例副本" for item in data.get("检查项", []))})
        checks.append({"名称": "包含212确认回执填写样例副本验证日志检查", "通过": any(item.get("名称") == "关键文件存在：212确认回执填写样例副本验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含213确认后路径演练报告验证通过检查", "通过": any(item.get("名称") == "213确认后路径演练报告验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含213确认后路径演练报告关键文件检查", "通过": any(item.get("名称") == "关键文件存在：213确认后路径演练报告" for item in data.get("检查项", []))})
        checks.append({"名称": "包含213确认后路径演练报告验证日志检查", "通过": any(item.get("名称") == "关键文件存在：213确认后路径演练报告验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含214正式回执待办卡验证通过检查", "通过": any(item.get("名称") == "214正式回执待办卡验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含214正式回执待办卡关键文件检查", "通过": any(item.get("名称") == "关键文件存在：214正式回执待办卡" for item in data.get("检查项", []))})
        checks.append({"名称": "包含214正式回执待办卡验证日志检查", "通过": any(item.get("名称") == "关键文件存在：214正式回执待办卡验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含215正式回执填写前自检验证通过检查", "通过": any(item.get("名称") == "215正式回执填写前自检验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含215正式回执填写前自检关键文件检查", "通过": any(item.get("名称") == "关键文件存在：215正式回执填写前自检" for item in data.get("检查项", []))})
        checks.append({"名称": "包含215正式回执填写前自检验证日志检查", "通过": any(item.get("名称") == "关键文件存在：215正式回执填写前自检验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含216正式回执录入后受控重跑预演验证通过检查", "通过": any(item.get("名称") == "216正式回执录入后受控重跑预演验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含216正式回执录入后受控重跑预演关键文件检查", "通过": any(item.get("名称") == "关键文件存在：216正式回执录入后受控重跑预演" for item in data.get("检查项", []))})
        checks.append({"名称": "包含216正式回执录入后受控重跑预演验证日志检查", "通过": any(item.get("名称") == "关键文件存在：216正式回执录入后受控重跑预演验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含206候选采用前闸口验证通过检查", "通过": any(item.get("名称") == "206候选采用前闸口验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含206候选采用前闸口关键文件检查", "通过": any(item.get("名称") == "关键文件存在：206候选采用前闸口" for item in data.get("检查项", []))})
        checks.append({"名称": "包含206候选采用前闸口验证日志检查", "通过": any(item.get("名称") == "关键文件存在：206候选采用前闸口验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含207候选采用受控执行预案验证通过检查", "通过": any(item.get("名称") == "207候选采用受控执行预案验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含207候选采用受控执行预案关键文件检查", "通过": any(item.get("名称") == "关键文件存在：207候选采用受控执行预案" for item in data.get("检查项", []))})
        checks.append({"名称": "包含207候选采用受控执行预案验证日志检查", "通过": any(item.get("名称") == "关键文件存在：207候选采用受控执行预案验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含208候选采用预览验证通过检查", "通过": any(item.get("名称") == "208候选采用预览验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含208候选采用预览关键文件检查", "通过": any(item.get("名称") == "关键文件存在：208候选采用预览" for item in data.get("检查项", []))})
        checks.append({"名称": "包含208候选采用预览验证日志检查", "通过": any(item.get("名称") == "关键文件存在：208候选采用预览验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含209受控写入命令草案验证通过检查", "通过": any(item.get("名称") == "209受控写入命令草案验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含209受控写入命令草案关键文件检查", "通过": any(item.get("名称") == "关键文件存在：209受控写入命令草案" for item in data.get("检查项", []))})
        checks.append({"名称": "包含209受控写入命令草案验证日志检查", "通过": any(item.get("名称") == "关键文件存在：209受控写入命令草案验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含198填写质量闸口验证通过检查", "通过": any(item.get("名称") == "198填写质量闸口验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含198填写质量闸口关键文件检查", "通过": any(item.get("名称") == "关键文件存在：198填写质量闸口" for item in data.get("检查项", []))})
        checks.append({"名称": "包含198填写质量闸口验证日志检查", "通过": any(item.get("名称") == "关键文件存在：198填写质量闸口验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含197完成后预演检查验证通过检查", "通过": any(item.get("名称") == "197完成后预演检查验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含197完成后预演检查关键文件检查", "通过": any(item.get("名称") == "关键文件存在：197完成后预演检查" for item in data.get("检查项", []))})
        checks.append({"名称": "包含197完成后预演检查验证日志检查", "通过": any(item.get("名称") == "关键文件存在：197完成后预演检查验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含194模板同步执行验证通过检查", "通过": any(item.get("名称") == "194模板同步执行验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含194模板同步执行报告关键文件检查", "通过": any(item.get("名称") == "关键文件存在：194模板同步执行报告" for item in data.get("检查项", []))})
        checks.append({"名称": "包含194模板同步执行验证日志检查", "通过": any(item.get("名称") == "关键文件存在：194模板同步执行验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含股票四系统闭环完成观察记录验证通过检查", "通过": any(item.get("名称") == "股票四系统闭环完成观察记录验证通过" for item in data.get("检查项", []))})
        checks.append({"名称": "包含股票四系统闭环完成观察记录关键文件检查", "通过": any(item.get("名称") == "关键文件存在：股票四系统闭环完成观察记录" for item in data.get("检查项", []))})
        checks.append({"名称": "包含股票四系统闭环完成观察记录验证日志检查", "通过": any(item.get("名称") == "关键文件存在：股票四系统闭环完成观察记录验证日志" for item in data.get("检查项", []))})
        checks.append({"名称": "包含文稿质检观察面板关键文件检查", "通过": any(item.get("名称") == "关键文件存在：文稿质检观察面板" for item in data.get("检查项", []))})
        checks.append({"名称": "包含文稿质检样本复盘报告关键文件检查", "通过": any(item.get("名称") == "关键文件存在：文稿质检样本复盘报告" for item in data.get("检查项", []))})
        checks.append({"名称": "包含文稿质检样本复盘验证脚本检查", "通过": any(item.get("名称") == "关键文件存在：文稿质检样本复盘验证脚本" for item in data.get("检查项", []))})
        checks.append({"名称": "包含接续边界检查", "通过": any(item.get("名称") == "施工接续边界写入日志" for item in data.get("检查项", []))})
        safety = data.get("安全边界", {})
        checks.append({"名称": "安全边界全部为False", "通过": all(value is False for value in safety.values())})
        checks.append({"名称": "明确不更新施工接续包", "通过": safety.get("更新施工接续包") is False})
    ok = all(item["通过"] for item in checks)
    print(json.dumps({"状态": "完成", "通过数量": sum(1 for item in checks if item["通过"]), "失败数量": sum(1 for item in checks if not item["通过"]), "检查项": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
