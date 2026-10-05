# mdslides

Markdown 进，**单个** HTML 幻灯片文件出。无 CDN、无外部字体、无构建步骤——双击就能放映。

## 快速开始

```bash
python -m mdslides examples/demo.md -o deck.html
# 或
python mdslides.py examples/demo.md -o deck.html --title "我的分享" --theme light
```

幻灯片以独占一行的 `---` 分隔。

## 放映操作

| 按键 | 动作 |
|---|---|
| → / 空格 / 点击 | 下一页 |
| ← | 上一页 |
| Home / End | 首页 / 末页 |
| f | 全屏 |
| n | 显示/隐藏讲稿 |

讲稿写在幻灯片源码里：`<!-- note: 这里是讲稿 -->`，按 `n` 呼出。

URL hash 会同步当前页码（`deck.html#3` 直达第 3 页）。打印（Ctrl+P）时所有幻灯片自动堆叠成文档。

## 支持的 Markdown 子集

- `#` / `##` / `###` 标题
- `-` 无序列表、`1.` 有序列表
- **粗体**、*斜体*、`` `行内代码` ``
- ``` 代码块、 `>` 引用
- `![alt](src)` 图片、`[text](url)` 链接

## 诚实说明

- **只支持上面列出的子集**：表格、任务列表、脚注、LaTeX 公式等都不支持，写了会按普通段落原样输出。
- 幻灯片分隔符 `---` 必须独占一行；代码块里的 `---` 不会被误切。
- 图片用相对路径，和 HTML 放同一目录即可；不会内嵌成 base64（保持文件小）。
- 纯标准库，Python 3.8+ 可跑。

## License

MIT
