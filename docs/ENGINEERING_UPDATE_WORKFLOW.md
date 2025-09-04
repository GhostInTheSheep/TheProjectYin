### 工程标准更新与发布流程（Git/GitHub）

适用对象：本仓库后端（Python，`pyproject.toml`）与前端（Electron/React，`frontend/Frontend-AI`）的日常更新、发版与部署。

---

## TL;DR｜最短指引
1) 从 `main` 新建分支；用 Conventional Commits 提交。
2) 本地跑质量门禁（lint/build/test），确认无报错。
3) 升级版本号（后端与前端同时），更新 CHANGELOG。
4) 提交 `chore(release): vX.Y.Z`，Push 并发起 PR。
5) 合并后打 Git tag、推送 tag，并创建 GitHub Release。
6) 可选：构建/推送 Docker 镜像，更新部署。

---

## 1. 分支与提交规范
- 分支命名：
  - 功能：`feat/<short-desc>`
  - 修复：`fix/<short-desc>`
  - 发布准备：`release/vX.Y.Z`
- 提交信息（Conventional Commits）：
  - `feat: 新增…`
  - `fix: 修复…`
  - `chore: 非业务改动（依赖/脚本/构建等）`
  - `docs: 文档`
  - `refactor: 重构`
  - `perf: 性能`
  - `test: 测试`

示例：
```bash
git checkout -b feat/responsive-control-panel
# 修改代码
git add -A
git commit -m "feat(ui): 控制面板小屏改为全屏单列响应式布局"
```

---

## 2. 本地质量门禁
在根目录执行（按需选择）：
```bash
# 后端依赖
pip install -r requirements.linux.txt

# 前端依赖
cd frontend/Frontend-AI && npm ci && cd -

# 前端构建
cd frontend/Frontend-AI && npm run build && cd -

# 可选：静态检查/格式化（若配置了）
ruff . || true
eslint frontend/Frontend-AI --max-warnings=0 || true
```

---

## 3. 语义化版本与版本号更新
语义化版本：`MAJOR.MINOR.PATCH`
- 破坏性变更：MAJOR+1
- 新增向后兼容功能：MINOR+1
- 修复/小改动：PATCH+1

需要同时更新：
- 后端：`pyproject.toml` 中的 `version = "X.Y.Z"`
- 前端：`frontend/Frontend-AI/package.json` 中的 `version`

示例（前端用 npm 管理版本号但不自动打 tag）：
```bash
cd frontend/Frontend-AI
npm version patch --no-git-tag-version
cd -

# 后端手动编辑 pyproject.toml，将 version 改为新号
```

---

## 4. 更新 CHANGELOG
新增/变更/修复列在顶端，从新到旧：
```markdown
## vX.Y.Z - 2025-09-04
- feat: 控制面板小屏全屏单列响应式
- fix: 释放 WebSocket/AudioContext/MediaStream 资源
- perf: 降低树莓派渲染开销（移动端布局）
```
建议文件：根目录 `CHANGELOG.md`（若无则新建）。

---

## 5. 发起 PR
```bash
git add -A
git commit -m "chore(release): vX.Y.Z"
git push -u origin <your-branch>
```
在 GitHub 打开 PR，描述：
- 变更点（用户可见）
- 风险与回滚方案
- 测试/验证方式（截图或命令输出）

PR 合并策略：**Squash & Merge** 或 **Rebase & Merge**，保持主干清爽。

---

## 6. 打 Tag 与创建 Release
PR 合并到 `main` 后：
```bash
git checkout main
git pull
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```
然后在 GitHub → Releases 页面：
- 选择刚推送的 tag `vX.Y.Z`
- 填写 Release Notes（可直接复制 `CHANGELOG` 对应部分）

---

## 7.（可选）Docker 镜像与部署
构建镜像：
```bash
docker build -t <your-dockerhub-username>/theprojectyin:vX.Y.Z -f Dockerfile .
docker push <your-dockerhub-username>/theprojectyin:vX.Y.Z
```

Compose 更新：
```bash
docker compose pull
docker compose up -d
```

树莓派（ARM）建议单独构建多架构镜像（使用 `docker buildx`）。

---

## 8. 热修复（Hotfix）
1) 从 `main` 分出：`hotfix/vX.Y.Z+1`
2) 修复 → 提交 → 提 PR
3) 合并后 bump PATCH 版本，打 `vX.Y.Z+1` tag，按第 6 节发布

---

## 9. 回滚指南
若新版本故障：
```bash
# 回滚到上个稳定版本
git checkout main
git revert <merge-commit-sha>
git push origin main

# 或快速部署旧镜像
docker compose pull && docker compose up -d
```

---

## 10. 树莓派 + Firefox 备注
- 广告视频优先 WebM（VP8/VP9），MP4/H.264 需系统编解码器
- 若首播被静音拦截，先进行一次用户交互
- Live2D 在低端机建议降低分辨率与抗锯齿

---

## 11. PR 模板（复制到描述区即可）
```markdown
### 变更内容
- [ ] 功能 / [ ] 修复 / [ ] 文档 / [ ] 优化

### 说明
- 背景：
- 主要修改点：
- 风险与影响：
- 回滚方案：

### 验证清单
- [ ] 本地构建通过（前端/后端）
- [ ] 关键路径自测通过
- [ ] 版本号已更新（pyproject / package.json）
- [ ] CHANGELOG 已更新
```

---

## 12. 常用命令速查
```bash
# 同步主干
git checkout main && git pull

# 新建分支
git checkout -b feat/<short-desc>

# 推送并创建 PR
git push -u origin HEAD

# 打版本 Tag
git tag -a vX.Y.Z -m "Release vX.Y.Z" && git push origin vX.Y.Z
```

如需把以上步骤自动化，可后续引入：commit lint、release 脚本、CI 构建与发布工作流（GitHub Actions）。


