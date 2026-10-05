# Historial de cambios de Deye Open MCP

> Copia de https://developer.deyecloud.com/openmcp/docs/deye-open-mcp-changelog.html (sync 2026-10-05 15:52 UTC).

Deye Open MCP 更新历史 
 Deye Open MCP MCP Skill MCP 工具文档 更新历史 EN 
 更新历史
 Deye Open MCP 服务的版本更新记录。
 v1.2 2026-07-29 
 历史数据工具 (device_history / device_history_raw / station_history / station_history_power) 新增 page/size 分页参数，避免返回数据量过大导致 MCP 上下文溢出
 分页响应包含 _page / _size / _total_items / _total_pages 元数据，方便翻页遍历全部数据
 SKILL.md 历史工具参数表与响应示例同步更新，加入 page/size 参数及分页元数据
 SKILL.md 为全部工具添加请求与响应示例值，提升 AI 调用准确率
 MCP 工具文档页面 (deye-open-mcp-tools.html) 为 4 个历史工具新增 page/size 参数行
 更新 MCP 工具文档页面，完善所有工具的响应字段说明
 新增版本更新历史页面
 v1.1 2026-06-12 ~ 07-16 
 list_deye_endpoints 支持内联解析 body 参数的 $ref 引用
 MCP 工具文档页面动态解析真实工具签名
 Skill 文档完善：凭据获取入口、认证前置流程、多客户端安装方式
 支持 Tencent WorkBuddy / Openclaw / Hermes 一键安装 Skill
 多项线上稳定性修复
 v1.0 2026-06-09 ~ 06-10 
 项目正式上线，基于 Streamable HTTP 远程 MCP 协议
 封装 DeyeCloud 39 个业务 API 为 MCP tools，覆盖电站、设备、数据、告警、控制全部场景
 打包可分发的 Skill，兼容 Cursor / Claude Code / Codex 等主流客户端
 MCP 服务并发优化，保障高并发场景稳定性
 Deye Open MCP — 让 AI 直接使用 DeyeCloud 能力
