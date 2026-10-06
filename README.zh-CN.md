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

重要选择由你来做，Praxis 帮你推敲理由，你使用的 coding agent 完成你委托的实现。这既包括**产品设计**——用户会经历什么，也包括**技术设计**——职责、状态和数据流如何支撑这些体验。

假设你正在为一个本地、单用户应用添加持久化聊天记录：

> **你：** 我希望重启应用后，聊天记录还在。
>
> **(o.o) 理解**
>
> 持久化范围: 只需要在这台设备上重启后保留，还是也要在设备之间同步？
>
> **你：** 目前只需要这台设备。
>
> **(o-o) 设计**
>
> 产品设计 / 发送体验: 消息正在保存时，用户应该看到什么？保存失败时呢？
>
> **你：** 立即显示消息，标记为待保存。失败时保留输入，让用户重试。
>
> **(o-o) 设计**
>
> 技术设计 / 存储: 你打算怎样存储消息，什么时候把待保存改成已保存？
>
> **你：** 用 SQLite。先标记已保存，再在后台写入。
>
> **(o_^) 检查**
>
> 确认时机: SQLite 适合本地存储，失败后保留输入也支持重试。但在写入成功前标记已保存，会留下一个缺口：应用可能关闭，而这条“已保存”的消息仍只在内存中。你会怎样调整顺序？
>
> **你：** 数据库写入成功前保持待保存。失败时留下消息，允许重试。
>
> **(^_~) 修正**
>
> 写入顺序: 这个调整保留了你想要的即时反馈，也让“已保存”对应一次完成的写入。用重启检查确认已保存的消息仍在；另行模拟写入失败，检查消息是否保持未保存状态，并允许重试。
>
> **你：** 按这个方案实现，并运行重启和写入失败检查。
>
> **(^_^) 实现**
>
> 结果: 已实现待保存、已保存和重试行为。重启检查确认已保存的消息仍在；模拟写入失败后，消息保持未保存状态，并允许重试。突然断电的情况未测试。这次值得记住的区别：即时反馈可以先于持久化，“已保存”的确认必须在持久化完成后。

这是用于展示交互的示例，并非已执行的验收记录。

五个节点描述当前正在做什么，不是固定顺序。技术约束可能让你重新理解需求，修正后也可以再次检查。节点标题跟随你的对话语言。

需要帮助时，Praxis 会解释缺少的概念，或比较可行方案及其取舍。选定方案并委托实现后，常规工作继续推进。学习来自不断连接**你的理由 → 选定的设计 → 实际观察到的结果**。

## Praxis 帮你形成什么

工程品味，是更早识别出更好选择的能力。

它来自交互、失败恢复等产品选择，也来自职责归属、模块边界、失败处理等技术选择。每次都把决策和结果连接起来：

```text
理解需求
→ 提出方案
→ 检查问题
→ 修正方案
→ 选择并委托
→ 实现
→ 观察
→ 内化
→ 下一次做出更好的选择
```

需求或证据发生变化时，这个循环可以回到前面的讨论。

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

在 Codex 设置中打开 Hooks，审阅并信任 Praxis 的 hooks，以允许自动注入教学上下文。

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
