# Tmux Pane Management Cheat Sheet  

---

## 📋 🪄 Basics

> **Prefix = usually Ctrl+b**

| 🔷 Action | 🎹 Shortcut |
|-----------|-------------|
| 🔻 **Split Horizontally (top & bottom)** | `Prefix + "` |
| 🔷 **Split Vertically (side by side)** | `Prefix + %` |
| 🔍 **Zoom/Unzoom Current Pane (full screen)** | `Prefix + z` |
| 🔄 **Switch Between Panes** | `Prefix + ← ↑ ↓ →` |
| 🔁 **Cycle Through Panes** | `Prefix + o` |
| 🔢 **Show Pane Numbers** | `Prefix + q` |
| ❌ **Close (Kill) Current Pane** | `exit` or `Ctrl+d` |
| 🔀 **Swap Panes** | `Prefix + Ctrl+o` |

---

## 🔷 🎨 Layouts

| 🖼️ Action | 🎹 Shortcut |
|-----------|-------------|
| 🔃 **Cycle Through Layouts** | `Prefix + Space` |
| ➖ **Even-Horizontal Layout** | Cycle until it appears |
| ➕ **Even-Vertical Layout** | Cycle until it appears |
| 🧩 **Tiled Layout** | Cycle until it appears |

> 💡 Just keep pressing `Prefix + Space` until you find the layout you love! ❤️

---

## 🖱️ 🔧 Resize Panes

| 🪄 Action | 🎹 Shortcut |
|-----------|-------------|
| ↔️ **Resize With Arrow Keys (one step)** | `Prefix + ← ↑ ↓ →` |
| 🏎️ **Hold Arrows for Continuous Resize** | `Prefix + (hold) ← ↑ ↓ →` |
| 🖱️ **Enable Mouse Support** | Add to `~/.tmux.conf`:<br> `set -g mouse on` |

---

## 🖥️ 📝 Notes

- 🎹 `Prefix` = usually `Ctrl+b`
- 🛑 **Detach from tmux session:** `Prefix + d`
- 🔗 **Re-attach to session:**  

  ```bash
  tmux attach-session -t <session-name>
  ```

- 🪄 **List sessions:**  

  ```bash
  tmux ls
  ```

---

