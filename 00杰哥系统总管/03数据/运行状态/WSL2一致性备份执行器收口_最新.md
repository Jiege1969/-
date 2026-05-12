# WSL2一致性备份执行器收口

生成时间：2026-05-06 08:57:43 +08:00

## 执行器

- 脚本：D:\杰哥智能化系统\00杰哥系统总管\02脚本\维护\Invoke-WSL2ConsistentBackup.ps1
- SHA256：E2622CBC77A5BEAD5AEBDD3879F0D5CD483ADE7D40EAF88D6713C7FF0CCD7E36

## 安全开关

不带 -IUnderstandStopDockerAndWsl 运行时，脚本会拒绝执行并退出；已验证该路径不会停止服务。

## 进入受控窗口后的行为

- 记录窗口前 WSL/Docker 状态。
- 执行 wsl --shutdown。
- 等待所有 WSL 发行版退出 Running。
- 复制两个 VHDX 到 F 盘备份目录。
- 计算源/目标 SHA256 并写 manifest。
- 尝试启动 Docker Desktop。
- 只读 GET 验收 n8n/Ollama，并 TCP 验收 Redis。

## 本轮状态

脚本已落地、已语法校验、已验证无硬开关时拒绝执行；未进入停机窗口，未复制 VHDX。
