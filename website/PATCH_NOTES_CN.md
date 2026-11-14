# KATOUWA MODIS API 热修复（2026-11-14）

**原因（已确认）：** 旧 `agents/modis.py` 只接受 NASA `/MOD13Q1/dates` 的 JSON 顶层数组；NASA 实际响应常为 `{"dates": [...]}`，所以旧代码将正常响应误报为失败。

**修复：**
- 同时识别 `{"dates":[...]}` 和旧数组形式；检查日期字段结构并拒绝错误文档。
- 若缓存的是错误结构，可刷新对应 URL 的缓存，再试一次。
- 无真实数据仍会失败；不会生成虚构数据。
- 新增单元测试覆盖正确包装格式、坏数据和错误缓存恢复。

**已知限制：** 当前制作环境无法联网实际访问 NASA API；只能对照官方文档验证响应格式，并使用模拟响应完成离线测试。请在你的 Mac 上实际下载验证。

**怎样修复已经启动的网站：**
1. 下载 `KATOUWA_MODIS_Fix_2026-11-14.zip` 到 Downloads。
2. 在 Mac 终端粘贴：
```bash
cd ~/Downloads
unzip -o KATOUWA_MODIS_Fix_2026-11-14.zip -d KATOUWA_READY
```
3. 在现有 Streamlit 页面刷新浏览器，然后左侧选 P1 和 2024–2025 年尝试一次；成功后再选 P1 + P2、2019–2025。
4. 若提示其他新错误，复制 `Agent execution log` 即可。

参见 NASA ORNL 官方文档：https://modis.ornl.gov/data/modis_webservice.html
