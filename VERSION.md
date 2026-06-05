# 版本 v2.0.0 — 2026-06-03 16:40

## Git tag: `v2.0.0`

### 回退命令
```bash
cd C:/Users/Administrator/.wpscomate/agent/workspace/wps-baixiaosheng
git checkout v2.0.0
cd frontend && npm install && npx vite build
```

### 核心文件
| 文件 | 说明 |
|------|------|
| `frontend/src/App.jsx` | 主应用（纯内联样式布局） |
| `frontend/src/index.css` | 样式（表面/输入/滚动条/Markdown/动画） |
| `frontend/src/api.js` | API 调用层 |
| `frontend/src/main.jsx` | React 入口 |
| `frontend/vite.config.js` | Vite 构建配置（base: '/'） |
| `app.py` | Flask 后端（带 React 静态文件服务） |

### 设计特点
- 左侧220px侧边栏 + 主区域自适应
- 所有布局使用内联样式（`marginLeft:'auto',marginRight:'auto'` 居中）
- 欢迎内容最大900px，聊天/输入框最大800px
- 3列卡片网格，间距16px
- 支持 1080p / 1440p / 2K 分辨率
- 蓝色强调色 (#2468f2)，浅灰页面底色 (#f2f3f5)
- 14个 SVG 图标组件

### 已知待优化
- 响应式断点处理
- 移动端适配
- 暗色模式
