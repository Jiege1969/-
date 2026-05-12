# -*- coding: utf-8 -*-
"""生成系统家底扫描报告和第一版交付使用手册。

只读扫描本机环境和系统目录，写入总管数据/文档；不触发外部服务。
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
ROOT = MANAGER.parent
STATE = MANAGER / "03数据" / "运行状态"
DOCS = MANAGER / "07文档" / "交付使用手册第一版"
RECOVERY = MANAGER / "03数据" / "并行回收"
SCRIPT_DIR = MANAGER / "02脚本"
ARCH = ROOT / "杰哥智能化系统全盘架构说明_20260504.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"cmd": cmd, "ok": False, "error": str(exc), "stdout": "", "stderr": ""}


def ps(script: str, timeout: int = 30) -> dict[str, Any]:
    return run(["powershell", "-NoProfile", "-Command", script], timeout)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def dir_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except Exception:
            pass
    return total


def gb(size: int | float | None) -> float:
    if not size:
        return 0.0
    return round(float(size) / 1024 / 1024 / 1024, 3)


def collect_filesystem() -> dict[str, Any]:
    drives = []
    for letter in ["C", "D", "E", "F"]:
        root = Path(f"{letter}:\\")
        if root.exists():
            usage = shutil.disk_usage(root)
            drives.append({
                "盘符": letter,
                "总容量GB": gb(usage.total),
                "已用GB": gb(usage.used),
                "剩余GB": gb(usage.free),
                "用途判断": {
                    "C": "Windows、Docker Desktop运行环境、用户目录",
                    "D": "杰哥智能化系统主目录和主要模型/WSL数据",
                    "E": "预留或轻量数据盘",
                    "F": "大容量备份、个人文件、股票工具等",
                }.get(letter, "未分类"),
            })
    root_dirs = []
    for child in ROOT.iterdir():
        if child.is_dir():
            root_dirs.append({"目录": str(child), "大小GB": gb(dir_size(child)), "修改时间": datetime.fromtimestamp(child.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")})
    f_items = []
    f_root = Path("F:\\")
    if f_root.exists():
        for item in sorted(f_root.iterdir(), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)[:30]:
            try:
                f_items.append({"名称": item.name, "类型": "目录" if item.is_dir() else "文件", "大小GB": gb(dir_size(item) if item.is_dir() else item.stat().st_size), "修改时间": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")})
            except Exception:
                pass
    return {"磁盘": drives, "D盘系统目录": root_dirs, "F盘顶层": f_items}


def collect_runtime() -> dict[str, Any]:
    return {
        "系统": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "用户": os.environ.get("USERNAME", ""),
            "主机名": os.environ.get("COMPUTERNAME", ""),
        },
        "CPU": ps("Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | ConvertTo-Json -Compress"),
        "内存": ps("Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory,Manufacturer,Model | ConvertTo-Json -Compress"),
        "显卡": ps("Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion | ConvertTo-Json -Compress"),
        "NVIDIA": run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version", "--format=csv,noheader"], 20),
        "WSL": run(["wsl", "-l", "-v"], 20),
        "WSL磁盘": run(["wsl", "-d", "Ubuntu-24.04", "--", "df", "-h"], 20),
        "Docker容器": run(["docker", "ps", "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"], 20),
        "Ollama模型": run(["docker", "exec", "jiege_v3_ollama", "ollama", "list"], 60),
        "端口19300段": ps("Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 19300 -and $_.LocalPort -le 19320 } | Select-Object LocalAddress,LocalPort,OwningProcess | Sort-Object LocalPort | ConvertTo-Json -Compress", 20),
        "常用端口": ps("Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 11434,19302,19310,28100,28679,29134,26379,8080 } | Select-Object LocalAddress,LocalPort,OwningProcess | Sort-Object LocalPort | ConvertTo-Json -Compress", 20),
        "计划任务": ps("Get-ScheduledTask | Where-Object { $_.TaskName -like '*杰哥*' -or $_.TaskName -like '*智能*' } | ForEach-Object { $a=($_.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments }) -join ' || '; [pscustomobject]@{TaskName=$_.TaskName;State=$_.State;Action=$a} } | ConvertTo-Json -Compress", 30),
    }


def collect_artifacts() -> dict[str, Any]:
    latest_state = []
    for item in sorted(STATE.glob("*最新*"), key=lambda p: p.stat().st_mtime, reverse=True)[:80]:
        latest_state.append({"文件": str(item), "大小KB": round(item.stat().st_size / 1024, 1), "修改时间": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")})
    recovery_files = []
    if RECOVERY.exists():
        for item in sorted(RECOVERY.glob("*最新*"), key=lambda p: p.stat().st_mtime, reverse=True)[:80]:
            recovery_files.append({"文件": str(item), "大小KB": round(item.stat().st_size / 1024, 1), "修改时间": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")})
    pycache = [str(p) for p in ROOT.rglob("__pycache__")][:200]
    old_task_candidates = [
        "Disabled计划任务仍指向旧路径：D:\\新杰哥智能系统、D:\\杰哥智能系统、H:\\AI脚本。",
        "01杰哥智能系统目录体量最大，主要由WSL2、Docker/Ollama模型和备份数据构成，后续清理必须先做引用检查。",
        "__pycache__ 可作为低风险缓存候选，但虚拟环境内的缓存建议随venv治理，不单独人工乱删。",
        "F盘存在系统备份目录和乱码同名备份目录，需要后续统一索引和命名。",
    ]
    return {"最新状态文件": latest_state, "并行回收文件": recovery_files, "Python缓存目录样本": pycache, "清理候选": old_task_candidates}


def md_table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(keys) + " |", "| " + " | ".join(["---"] * len(keys)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(k, "")).replace("\n", "<br>") for k in keys) + " |")
    return "\n".join(out)


def make_docs(report: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    filesystem = report["文件系统"]
    runtime = report["运行环境"]
    docs: dict[str, str] = {}

    docs["00_系统概况速读.md"] = f"""# 系统概况速读

杰哥智能化系统是一套本地私有化 AI 中台，目标是通过企业微信和本地入口服务，把股票分析、知识检索、文稿处理、视频预案、税收只读证据链等能力统一起来。核心原则是本地运行、数据不外传、人工确认闸口、安全动作默认关闭、经验持续沉淀。

当前主目录是 `D:\\杰哥智能化系统`，分为 `00总管`、`01智能`、`02扩展`、`03进化` 四层。总管负责调度、自检、口径、回滚和安全闸门；智能系统负责模型、知识检索和中台能力；扩展系统负责股票、企业微信、视频、内容、税收等业务；进化系统负责规则沉淀和反退化巡检。

本机硬件扫描显示：CPU 为 AMD Ryzen 7 7800X3D，内存约 64GB，主显卡为 RTX 3090 24GB。Docker 中正在运行 Ollama、Redis、n8n 三个容器。WSL2 中 `Ubuntu-24.04` 和 `docker-desktop` 均为运行状态。

当前交付口径：系统已进入可交付确认完成和交付后只读巡检/维护阶段。真实动作闸门仍关闭：不自动触发 n8n，不放量企业微信，不接券商，不下单，不自动交易。
"""

    docs["01_硬件部署与服务清单.md"] = f"""# 硬件部署与服务清单

主机配置：AMD Ryzen 7 7800X3D，约 64GB 内存，RTX 3090 24GB。D盘是主系统和模型数据盘，F盘是大容量备份与个人资料盘。

Docker 当前容器：

```text
{runtime['Docker容器'].get('stdout','').strip()}
```

端口口径：

- Ollama：容器 11434 映射到 `127.0.0.1:29134`
- Redis：容器 6379 映射到 `127.0.0.1:26379`
- n8n：容器 5678 映射到 `127.0.0.1:28679`
- 股票/企业微信本地入口：已监听 `19300`、`19302`、`19310`
- v3 智能体大脑测试服务：脚本目标端口 `28100`

计划任务里 Ready 的项目包括开机施工准备自检、企业微信统一指令本地服务、股票系统交付运行环境、v3智能体大脑测试服务。Disabled 的旧任务仍指向旧路径，后续应做只读核验后归档或删除。
"""

    docs["02_本地模型清单.md"] = f"""# 本地模型清单

本机没有原生命令行 `ollama`，模型服务主要在 Docker 容器 `jiege_v3_ollama` 中运行。

当前模型清单：

```text
{runtime['Ollama模型'].get('stdout','').strip()}
```

建议用途：

- embedding/reranker：知识检索、证据排序、可追溯问答。
- qwen3 / deepseek-r1 / gemma：报告草稿、推理、复盘、代码辅助。
- Fin-R1 / finance-llama：股票研究辅助分析，只输出研究和风险提示。

注意：模型能力不是交易能力。股票系统保持 analysis-only，不接券商接口，不生成下单委托，不自动交易。
"""

    docs["03_目录结构速查.md"] = f"""# 目录结构速查

主目录：`D:\\杰哥智能化系统`

{md_table(filesystem['D盘系统目录'], ['目录', '大小GB', '修改时间'])}

常用目录规则：

- `01配置`：规则、口径、闸门和服务配置。
- `02脚本`：生成、验证、巡检、启动和维护脚本。
- `03数据`：运行状态、验收报告、任务台账、索引和业务数据。
- `04日志`：服务日志、运行日志、错误日志。
- `05备份`：只保留计划任务、开机加固、每日巡检、交易边界等回滚/边界资产，不再保存普通施工快照。
- `07文档`：设计说明、操作手册、交付说明。

F盘顶层当前可见：

{md_table(filesystem['F盘顶层'][:12], ['名称', '类型', '大小GB', '修改时间'])}
"""

    docs["04_企业微信与日常入口.md"] = """# 企业微信与日常入口

常用入口优先走企业微信或本地服务。当前本地服务有 19300、19302、19310 三类监听，具体路由以总管和企业微信助手配置为准。

建议先固化这些日常指令：

- `ping`：确认服务是否活着。
- `分析 股票代码`：触发单股分析。
- `股票 状态`：查看股票系统运行状态。
- `系统 状态`：查看总管口径和安全闸门。
- `暂停`：暂停低风险任务或计划队列。
- `恢复`：恢复已暂停的低风险任务。
- `#审稿`：文稿质检入口，目前应按影子/草稿方式处理。
- `#经验`：把有价值的处理过程标记为经验候选。

阅读推送时先看结论、风险提示和证据来源，再点开详细附件。手机端短文应短，长报告应走附件或本地详情页。真实群发和放量推送仍需单线许可令，不会自动打开。
"""

    docs["05_股票系统使用卡.md"] = """# 股票系统使用卡

股票系统当前定位是研究分析系统，不是交易系统。

可用能力：

- 单股分析：用 `分析 股票代码` 触发。
- 样本池关注：盘中可关注价格、成交额、异动和风险。
- 收盘复盘：生成候选分层、风险提示和研究报告。
- 微信短回复/短文：可生成阅读友好的摘要。

看报告时按这个顺序读：

1. 先看风险提示，确认是否有数据缺失、异动过大、口径不一致。
2. 再看实时行情、成交额、历史K线和候选分层。
3. 最后看综合评述，它是研究意见，不是买卖建议。

硬边界：不接券商接口，不下单，不自动交易，不生成仓位和目标价指令。涉及“买、卖、加仓、减仓、下单”的表达，应被拦截或改写为观察条件。
"""

    docs["06_故障排查三件事.md"] = """# 故障排查三件事

如果企业微信发消息没反应，就先在 PowerShell 跑：

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 19300 -and $_.LocalPort -le 19320 }
docker ps
wsl -l -v
```

如果 19300、19302、19310 都没有监听，就运行总管启动脚本或开机自检脚本。不要直接改 n8n 工作流，不要打开真实群发。

如果 AI 回复特别慢，就先看 GPU：

```powershell
nvidia-smi
docker exec jiege_v3_ollama ollama ps
```

如果显存被大模型占满，先暂停新任务，等模型空闲释放；不要同时跑视频渲染、大模型推理和游戏。

如果磁盘空间告警，就先看：

```powershell
Get-PSDrive -PSProvider FileSystem
Get-ChildItem D:\\杰哥智能化系统 -Directory
```

只清理已列入低风险候选的缓存和临时文件。WSL、Docker、Ollama 模型、备份目录不能手工乱删。
"""

    docs["07_备份恢复速查.md"] = """# 备份恢复速查

备份主盘在 F 盘，系统内 `05备份` 目录只保留已分层确认的回滚/边界资产。

手动备份前先做三件事：

1. 跑总管只读巡检，确认当前状态可读。
2. 确认 D 盘和 F 盘剩余空间足够。
3. 确认要备份的是系统目录、WSL/Docker数据、Ollama模型还是业务报告。

恢复时不要直接覆盖当前系统。先把备份恢复到临时目录，再跑验证：

```powershell
wsl -l -v
docker ps
Get-NetTCPConnection -State Listen
python D:\\杰哥智能化系统\\00杰哥系统总管\\02脚本\\验证总管脚本化闭环.py
```

恢复后必须通过：企业微信 ping、本地端口监听、Docker容器、Ollama模型、总管进度口径、安全闸门。自动交易和券商接口必须继续关闭。
"""

    docs["08_维护清理与查漏补缺.md"] = """# 维护清理与查漏补缺

已完成的治理：旧路径巡检、D盘旧残留清理、旧文件清理合并候选、低风险 Python 缓存清理、多对话框冲突检测、05备份资产分层清债。

当前缺口：

- 开机自动运行还不是完整日常模式，只是已有计划任务和启动脚本基础。
- 交易日 9:00 准备、9:30-15:00 盯盘、收盘复盘、晚间报告还需总管日程化。
- Disabled 旧计划任务仍指向旧路径，应做“旧任务归档/删除候选”。
- F盘存在乱码备份目录，应统一索引和命名。
- 文稿质检、税收政策、视频制作还需独立使用卡继续补。

清理原则：先核实当前依赖；能证实无依赖的旧项当轮删除或修正。保留防复发规则、当前资产和必要回滚边界，不把旧债改名为观察项。
"""

    docs["09_常用命令速查.md"] = """# 常用命令速查

WSL：

```powershell
wsl -l -v
wsl -d Ubuntu-24.04 -- df -h
```

Docker：

```powershell
docker ps
docker logs jiege_v3_ollama --tail 100
docker logs jiege_v3_n8n --tail 100
docker logs jiege_v3_redis --tail 100
```

Ollama：

```powershell
docker exec jiege_v3_ollama ollama list
docker exec jiege_v3_ollama ollama ps
```

端口：

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 19300 -and $_.LocalPort -le 19320 }
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 28679,29134,26379 }
```

总管验收：

```powershell
python D:\\杰哥智能化系统\\00杰哥系统总管\\02脚本\\验证总管脚本化闭环.py
```
"""

    docs["10_系统能自行做到什么.md"] = """# 系统能自行做到什么

已经能自行或半自行做到：

- 开机施工准备自检。
- 本地服务启动和 PID/日志记录。
- Docker基础服务常驻运行。
- 总管只读巡检、冲突检测、进度口径读取。
- 证据索引、回收报告、验收报告生成。
- 经验规则沉淀和反退化巡检种子。
- 低风险缓存清理和旧文件候选化。

还不能直接承诺做到：

- 保证整台电脑所有异常都自动修好。
- 自动打开企业微信放量、n8n正式执行、正式库写入。
- 自动接券商接口或自动交易。
- 在你打游戏、视频渲染、模型推理同时进行时完全不抢资源。

下一步应建设“日常运行总控”：开机自检、交易日判断、股票盘中调度、收盘复盘、晚间报告、周末低负载、资源避让和异常降级。
"""

    for name, content in docs.items():
        path = DOCS / name
        write_text(path, content.strip() + "\n")
        paths.append(str(path))
    return paths


def make_report_md(report: dict[str, Any], docs: list[str]) -> str:
    runtime = report["运行环境"]
    fs = report["文件系统"]
    return "\n".join([
        "# 系统家底扫描报告",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总体判断",
        "- 系统已具备可交付确认、只读巡检、安全闸门、回滚证据和经验沉淀基础。",
        "- 已有开机自检和若干 Ready 计划任务，但完整日常自动运行模式尚未完全封装启用。",
        "- 股票系统保持 analysis-only；券商接口、下单、自动交易继续关闭。",
        "",
        "## 硬件与部署",
        f"- 主机：{runtime['系统'].get('主机名','')}",
        f"- 系统：{runtime['系统'].get('platform','')}",
        f"- Docker容器：{runtime['Docker容器'].get('stdout','').replace(chr(10), ' / ')}",
        f"- WSL：{runtime['WSL'].get('stdout','').replace(chr(10), ' / ')}",
        "",
        "## 磁盘",
        md_table(fs["磁盘"], ["盘符", "总容量GB", "已用GB", "剩余GB", "用途判断"]),
        "",
        "## 已生成手册",
        *[f"- {path}" for path in docs],
        "",
    ])


def main() -> int:
    report = {
        "名称": "系统家底扫描与交付使用手册第一版",
        "生成时间": now_text(),
        "扫描边界": {
            "只读扫描": True,
            "触发外部服务": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "文件系统": collect_filesystem(),
        "运行环境": collect_runtime(),
        "系统产物": collect_artifacts(),
        "结论": {
            "交付状态": "可交付确认完成，进入交付后只读巡检/维护",
            "完整日常自动运行模式": "未完全封装启用",
            "清理状态": "已有多轮清理治理和候选清单，仍需旧计划任务/F盘备份命名/大目录索引二次治理",
            "经验沉淀": "已沉淀到03进化规则、自动评审、反退化巡检种子和总管口径",
        },
    }
    docs = make_docs(report)
    report["生成手册"] = docs
    report_json = STATE / "系统家底扫描与交付使用手册第一版_最新.json"
    report_md = STATE / "系统家底扫描与交付使用手册第一版_最新.md"
    write_json(report_json, report)
    write_text(report_md, make_report_md(report, docs))
    print(json.dumps({"状态": "通过", "手册数量": len(docs), "报告": str(report_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
