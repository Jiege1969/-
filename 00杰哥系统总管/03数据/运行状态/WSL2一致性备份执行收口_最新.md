# WSL2一致性备份执行收口

生成时间：2026-05-06 09:41:58 +08:00

## 结论

WSL2 VHDX 一致性备份已完成。执行过程中先停止 Docker/WSL，确认 WSL 发行版为 Stopped 后复制 VHDX；源/目标 SHA256 全部匹配，不是热拷。

## 备份目录

F:\系统备份\WSL2一致性备份_20260506_090045

## 文件

- docker_data.vhdx：117365014528 bytes，SHA256 8F8306B196C780A9923C25E6CE402159E8F33D27ACB672A53CC3E6F3A9F410B0
- ext4.vhdx：85931851776 bytes，SHA256 BD08232A7320EB7EBC753037F1B8D2EE0337083B8C2994CD42EA3871C850E5A8
- manifest：F:\系统备份\WSL2一致性备份_20260506_090045\backup_manifest.json

## 重启后验收

- n8n：200
- Ollama：200
- Redis TCP：True

## 台账

已更新 F:\系统备份\备份总台账_最新.md/json。

## 安全边界

未触发 n8n 工作流，未发送企业微信，未调用券商接口，未自动交易，未删除数据。
