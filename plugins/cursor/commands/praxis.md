---
name: praxis
description: Enable, disable, or inspect Praxis for the current project.
---

Handle the explicit Praxis control action from this command invocation.

Supported forms:

```text
/praxis enable
/praxis disable
/praxis status
```

Interpret only the control word after `/praxis`.

- For `enable`, run `praxis enable --cwd .`.
- For `disable`, run `praxis disable --cwd .`.
- For `status`, run `praxis status --cwd .`.
- If the control word is missing or unsupported, show the three supported forms and do nothing.
- Report the resulting enabled/disabled state concisely.
- Do not treat this control action as approval of any engineering decision.
- Do not ask the user to run the underlying CLI themselves.
