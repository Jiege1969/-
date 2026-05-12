# WSL2一致性备份执行前核验

生成时间：2026-05-06 08:55:20 +08:00

## 结论

通过执行前核验，但未执行备份。原因不是拖延，而是当前 docker-desktop 与 Ubuntu-24.04 正在 Running，两个 VHDX 仍在变化；热拷会制造不可靠备份，违反一致性规则。

## 资产

- D:\杰哥智能化系统\01杰哥智能系统\03数据\WSL2\docker-desktop\disk\docker_data.vhdx：109.3 GB，LastWrite=2026-05-06 08:55:07
- D:\杰哥智能化系统\01杰哥智能系统\03数据\WSL2\Ubuntu-24.04\ext4.vhdx：80.03 GB，LastWrite=2026-05-06 08:55:12

合计：189.33 GB

## 空间

- F 盘可用：3626.25 GB
- 目标模板：F:\系统备份\WSL2一致性备份_20260506_085520
- 空间结论：True

## 可执行窗口步骤

- 记录窗口前血脉探针与Docker状态
- 暂停写入型计划任务或确认窗口内无施工
- 停止Docker Desktop或执行 wsl --shutdown
- 确认 wsl --list --verbose 无 Running 发行版
- 复制两个VHDX到F盘目标目录
- 计算源/目标文件大小与SHA256
- 启动Docker Desktop/WSL
- 验收n8n/Ollama/Redis/血脉探针
- 更新F盘备份总台账

## 本轮未执行项

未停止 Docker/WSL，未复制 VHDX，未对运行中的 VHDX 计算哈希，未热拷。

## 执行器

- 脚本：D:\杰哥智能化系统\00杰哥系统总管\02脚本\维护\Invoke-WSL2ConsistentBackup.ps1
- SHA256：E2622CBC77A5BEAD5AEBDD3879F0D5CD483ADE7D40EAF88D6713C7FF0CCD7E36
- 安全开关：必须带 -IUnderstandStopDockerAndWsl 才会进入停机备份流程；无开关已验证拒绝执行。

