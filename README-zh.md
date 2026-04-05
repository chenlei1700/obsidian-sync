# obsidian-sync

**一个 Claude Code 插件：一条命令，将项目文档同步到 Obsidian vault 统一管理。零配置。**

[English](README.md)

---

## 解决什么问题

你 clone 了很多项目。每个项目里散落着各种 `.md` 文件——README、设计文档、使用指南、API 文档——藏在层层嵌套的目录里。你想在一个地方阅读和检索它们，但它们分布在几十个项目文件夹中。

**obsidian-sync** 一条命令，把项目中所有 Markdown 文件同步到你的 Obsidian vault，同时保持项目中的正常访问。

## 工作原理

```
项目目录/                                Obsidian vault/projects/项目名/
  ai/gnn/docs/SETUP.md      ──→         ai-gnn-docs/SETUP.md
  docs/设计���档.md             ──���         docs/设计文档.md
  README.md                  ─��→         README.md
```

1. **扫描** 项目中所有 `.md` 文件
2. **扁平化** 深层目录路径为可读的单级文件夹（`a/b/c/file.md` → `a-b-c/file.md`）
3. **移动** 文件到 vault 并在原位置创建 **符号链接**（或复制，你选）
4. **追踪** 同步状态——可以安全地重复运行

## 快速开始

### 安装

```bash
claude plugins add github.com/chenlei/obsidian-sync
```

### 使用

在任意项目目录下使用 Claude Code：

```bash
# 预览将要同步的内容（首次推荐）
/obsidian-sync --dry-run

# 使用符号链接同步（默认）
/obsidian-sync

# 使用复制模式（无需特殊权限）
/obsidian-sync --mode copy
```

也可以直接运行脚���：

```bash
python sync_to_obsidian.py --dry-run
python sync_to_obsidian.py
```

**零配置**——脚本自动检测：
- 项目目录（当前工作目录）
- 项目名（从 `git remote` 或文件夹名）
- Obsidian vault 位置（从 Obsidian 配置文件读取）

## 同步模式

| 模式 | 工作方式 | 要求 |
|------|---------|------|
| **symlink**（默认） | 文件移到 vault，项目中创建符号链接 | Windows 需开启开发者模式 |
| **copy** | 文件复制到 vault，原文件不动 | 无 |

symlink 模式下，链接对 git、编辑器、代码引用完全透明——文件物理位置在 vault 中，但使用体验不变。

如果 symlink 不可用，脚本会告诉你如何开启并退出。不会静默降级。

## 参数选项

全部可选——零参数即可运行。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--project-dir 路径` | 项目根目录 | 当��目录 |
| `--vault-dir 路径` | Obsidian vault 路径 | 自动检测 |
| `--project-name 名称` | 在 vault 中的项目文件夹名 | 从 git remote / 目录名推导 |
| `--mode {symlink,copy}` | 同���策略 | `symlink` |
| `--dry-run` | 仅预览，不执行 | 关闭 |

## 同步范围

**同步**：项目中所有 `.md` 文件。

**自动排除：**
- `CLAUDE.md` — Claude Code 配置文件
- `.claude/`、`.git/`、`.github/`
- `node_modules/`、`venv/`、`.venv/`、`env/`
- `build/`、`dist/`、`__pycache__/`、`.pytest_cache/`

## 路径扁平化

深层目录嵌套会被合并为扁平、可读的文件夹名：

| 原路径 | vault 中 |
|--------|---------|
| `README.md` | `README.md` |
| `docs/guide.md` | `docs/guide.md` |
| `src/api/docs/SETUP.md` | `src-api-docs/SETUP.md` |
| `a/b/c/d/notes.md` | `a-b-c-d/notes.md` |

单级目录保持不变，仅多级路径会被扁平化。

## Vault 结构

同步多个项目后：

```
Obsidian Vault/
  projects/
    my-app/
      .sync-manifest.json
      README.md
      docs/
      src-components-docs/
    another-repo/
      .sync-manifest.json
      README.md
      api-docs/
```

每个项目隔离在自己的文件夹中。`.sync-manifest.json` 记录同步状态和时间。

## 平台支持

| 平台 | symlink 模式 | copy 模�� |
|------|-------------|-----------|
| Windows（开发者模式开启） | 支持 | 支持 |
| Windows（开发者模式关闭） | 不支持（有明确提示） | 支持 |
| macOS | 支持 | 支持 |
| Linux | 支持 | ��持 |

## 环境要求

- Python 3.10+
- 已安装 Obsidian（用于自动检测 vault 路径）
- Claude Code（作为插件使用）——也可独立运行脚本

## 许可证

MIT
