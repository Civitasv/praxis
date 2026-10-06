<p align="center">
  <img src=".github/assets/praxis-mark.svg" width="96" height="96" alt="Praxis">
</p>

<h1 align="center">Praxis</h1>

<p align="center"><strong>和 AI 一起写代码，也培养自己的工程品味。</strong></p>

<p align="center">
  一个帮助你在 AI 编程过程中形成工程品味的插件。
</p>

<p align="center">
  <sub>Codex · Cursor · CodeBuddy · DeepSeek Harness</sub>
</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

---

## 理念

**AI 让实现变得廉价，但工程品味仍然需要自己获得。**

产出得快，不等于工程做得好。如果每个重要选择都由 AI 在你理解之前替你完成，你也许今天交付得更快，却没有变得更擅长做明天的决定。

Praxis 扩展你已经在使用的 coding agent。机械性的工作继续快速推进；当一个决定足以影响系统时，Praxis 会让节奏慢下来一点，把背后的理由、备选方案、权衡和后果暴露出来。

这些理解会积累。你理解过的好决策越多，就越能更早地自己识别它们。

**在正确的地方慢一点，长期反而更快。**

## 使用 Praxis 是什么感觉

没有 Praxis：

```text
你      添加持久化聊天记录。

Agent   我会让数据库作为 source of truth，
        Redis 作为缓存。

        ✓ 已实现
```

启用 Praxis：

```text
你      添加持久化聊天记录。

Agent   我会让数据库作为 source of truth，
        Redis 作为缓存。

        这个选择很重要：
        聊天记录属于持久化产品数据，
        Redis 重启不应该让用户丢失历史记录。

        代价是多了一条持久化写入路径，
        但 Redis 仍然可以是可丢弃的。

你      我不理解 source of truth 是什么意思。

Agent   意思是数据库拥有权威版本的聊天历史。
        Redis 可以让读取更快，但 Redis 丢失时，
        消息本身不应该丢失。

你      明白了。

Agent   ✓ 已实现
        ✓ 已验证：Redis 重启后聊天历史仍然存在
```

Praxis 把学习留在原本的开发流程里，让这个决定逐渐成为你自己的工程品味，而不是消失在 AI 生成的实现里。

## Praxis 帮你形成什么

工程品味，是更早识别出更好选择的能力。

它来自不断把决策和结果连接起来：

```text
比较
→ 选择
→ 实现
→ 观察
→ 内化
→ 下一次做出更好的选择
```

Praxis 不会让整个任务都变慢。它只在值得理解的地方投入注意力，让这些理解不断复利，使未来的决策更快、更好，也更独立。

## 安装

需要 Python 3.10+。

安装 Praxis：

```bash
python3 -m pip install --user 'git+https://github.com/Civitasv/praxis.git'
```

Windows 下将 `python3` 替换为 `py`。

然后把 Praxis 添加到你使用的 coding agent。

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add Civitasv/praxis
codex plugin add praxis@praxis
```

在项目中启用：

```text
$praxis:praxis-enable
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

```bash
mkdir -p ~/.cursor/plugins/local
git clone --depth 1 https://github.com/Civitasv/praxis.git ~/.cursor/plugins/local/praxis
```

重启 Cursor，然后运行：

```text
/praxis enable
```

</details>

<details>
<summary><strong>DeepSeek Harness / Cordis</strong></summary>

将 `web` 替换为你的 profile 名称。

```bash
dsh plugin --profile web add github:Civitasv/praxis
dsh --profile web
```

然后运行：

```text
/praxis enable
```

</details>

<details>
<summary><strong>CodeBuddy</strong></summary>

```bash
codebuddy plugin marketplace add Civitasv/praxis --name praxis && codebuddy plugin install praxis@praxis
```

然后运行：

```text
/praxis:enable
```

</details>

启用后正常工作即可。Praxis 只会在值得学习的决策上让节奏慢下来。

## 命令

| Agent | 启用 | 禁用 | 状态 |
| --- | --- | --- | --- |
| Cursor | `/praxis enable` | `/praxis disable` | `/praxis status` |
| DeepSeek Harness | `/praxis enable` | `/praxis disable` | `/praxis status` |
| CodeBuddy | `/praxis:enable` | `/praxis:disable` | `/praxis:status` |
| Codex | `$praxis:praxis-enable` | `$praxis:praxis-disable` | `$praxis:praxis-status` |

## 更新 Praxis

更新 Praxis：

```bash
python3 -m pip install --user --upgrade 'git+https://github.com/Civitasv/praxis.git'
```

然后刷新你使用的集成。

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace upgrade praxis
codex plugin add praxis@praxis
```

打开一个新的聊天。

</details>

<details>
<summary><strong>Cursor</strong></summary>

```bash
git -C ~/.cursor/plugins/local/praxis pull --ff-only
```

重启 Cursor。

</details>

<details>
<summary><strong>DeepSeek Harness / Cordis</strong></summary>

```bash
dsh plugin --profile web update praxis
dsh --profile web
```

</details>

<details>
<summary><strong>CodeBuddy</strong></summary>

```bash
codebuddy plugin marketplace update praxis && codebuddy plugin update praxis@praxis
```

然后重新加载插件：

```text
/reload-plugins
```

</details>

## 状态

Praxis 目前处于 **alpha** 阶段。

当前支持：Codex、Cursor、CodeBuddy 和 DeepSeek Harness / Cordis。目前通过源码分发。

## License

Praxis 使用 **GNU Affero General Public License v3.0（AGPL-3.0-only）**。

你可以使用、修改和再分发 Praxis；当 AGPL 的 copyleft 条件被触发时，对 Praxis 的修改及相应源码需要继续以兼容的开源方式提供。对于通过网络提供修改版本的场景，AGPL 还包含额外的源码提供义务。完整条款见 [LICENSE](LICENSE)。

## 文档

实现细节位于 `Docs/`：

- [架构概览](Docs/Architecture/Overview.md)
- [Tutor 模型](Docs/Architecture/Tutor%20Model.md)
- [Harness 集成](Docs/Architecture/Harness%20Integration.md)
- [Feature Specs](Docs/Specs/)
- [开发与验证](Docs/Development/Validation.md)

贡献者建议从 [Code.md](Code.md) 和 [State.md](State.md) 开始。
