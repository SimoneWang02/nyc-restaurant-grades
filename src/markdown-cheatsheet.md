<!-- Delete or move after finished project -->

# Markdown Cheatsheet

Part 1 is plain Markdown, which works anywhere (GitHub, VS Code, Framework). Part 2 covers the extras that only work in Observable Framework pages (files in `src/`).

---

## Part 1. Plain Markdown

### Headings

```md
# Heading 1 (page title, use once per page)

## Heading 2

### Heading 3
```

### Text

```md
**bold**
_italic_
~~strikethrough~~
`inline code`
```

A blank line starts a new paragraph. A single line break inside a paragraph is ignored.

### Links and images

```md
[link text](https://example.com)
[another page on the site](./q1)
![alt text](images/chart.png)
```

### Lists

```md
- bullet
- bullet
    - nested bullet (indent 2 spaces)

1. first
2. second
3. third
```

### Quotes

```md
> A quoted line.
```

### Code blocks

````md
```python
df = pd.read_csv("data/raw/file.csv")
```
````

The word after the backticks (`python`, `js`, `sh`, `css`) sets the syntax highlighting.

### Tables

```md
| score |     n |
| ----- | ----: |
| 12    | 5,721 |
| 13    | 4,784 |
```

`:` sets the alignment: `|:---|` left, `|:---:|` center, `|---:|` right.

### Horizontal line

```md
---
```

### Comments (hidden from the page)

```md
<!-- this does not show up -->
```

### Escaping

Put a backslash before a character to show it literally: `\*not italic\*`, `\#`.

---

## Part 2. Observable Framework extras

### Front matter (page settings)

Goes at the very top of a page, between `---` lines.

```md
---
title: Earning an A
toc: false
---
```

| Key       | What it does                                        |
| --------- | --------------------------------------------------- |
| `title`   | Browser tab title (default: the first `#` heading)  |
| `toc`     | `false` hides the "Contents" box on the right       |
| `sidebar` | `false` hides the sidebar on this page              |
| `pager`   | `false` hides the previous/next links at the bottom |

### JavaScript blocks

A code block marked `js` **runs** in the page:

````md
```js
const data = FileAttachment("data/q1_scores.csv").csv({ typed: true });
```
````

| Block               | Result                                   |
| ------------------- | ---------------------------------------- |
| ` ```js `           | Runs the code; the code itself is hidden |
| ` ```js echo `      | Runs it and also shows the code          |
| ` ```js run=false ` | Shows the code without running it        |

If the last line of a block is a bare expression (not `const x = ...`), its value is shown on the page.

### Showing things on the page

```js run=false
display(chart); // show a chart, element or value
display(data); // shows an inspector you can expand, handy for checking data
```

### Inline values in text

```md
There were ${data.length} rows.
```

### Loading data

Paths are relative to the page file. A leading `/` means "from `src/`".

```js run=false
const csv = FileAttachment("data/q1_scores.csv").csv({ typed: true }); // typed: numbers become numbers
const json = FileAttachment("data/q1_meta.json").json();
const text = FileAttachment("data/notes.txt").text();
```

The file name must be a plain string written in the code, not built from variables, so Framework can find it at build time.

### Imports

```js run=false
import { scoreHistogram } from "./components/scoreHistogram.js";
```

`d3`, `Inputs`, `html`, `svg` and `width` are built in. You do not need to import them.

### Width (for responsive charts)

```js run=false
display(myChart(d3, data, { width }));
```

`width` is the width of the main column. Blocks that use it rerun when the window is resized.

### Reactivity

Blocks rerun when a variable they use changes, like an Observable notebook. Block order on the page does not matter. Each top-level `const` can only be defined once per page.

### Inputs (interaction)

```js run=false
const cutoff = view(
	Inputs.range([0, 30], { step: 1, value: 13, label: "Cutoff" }),
);
```

```js run=false
display(myChart(d3, data, { width, cutoff })); // reruns when the slider moves
```

Live example (this one runs):

```js echo
const demoCutoff = view(Inputs.range([0, 30], { step: 1, value: 13, label: "Cutoff" }));
```

The cutoff is ${demoCutoff}, so a score of 14 is ${14 <= demoCutoff ? "an A" : "not an A"}.

Other inputs: `Inputs.select(options)`, `Inputs.radio(options)`, `Inputs.checkbox(options)`, `Inputs.toggle()`, `Inputs.search(data)`, `Inputs.table(data)`.

### Notes and callouts

```html
<div class="note">A note.</div>
<div class="tip">A tip.</div>
<div class="warning">A warning.</div>
<div class="caution">A caution.</div>
```

Leave a blank line after the opening tag if you want Markdown to work inside:

```html
<div class="note">Markdown such as **bold** works here.</div>
```

### Cards and grid layout

```html
<div class="grid grid-cols-2">
	<div class="card">${chart1}</div>
	<div class="card">${chart2}</div>
</div>
```

Use `grid-cols-1` to `grid-cols-4`.

### Page-only CSS

```html
<style>
	h1 {
		max-width: none;
	}
</style>
```

Affects only the page it is on.

### Links between pages

```md
[Question 1](./q1)
```

Leave off `.md`. The build checks these links and warns if a page does not exist.

---

## Commands

```sh
npm run dev      # live preview at http://127.0.0.1:3000
npm run build    # build the site into dist/
npm run clean    # clear the Framework cache
```

## Reference

- Markdown in Framework: https://observablehq.com/framework/markdown
- JavaScript in Framework: https://observablehq.com/framework/javascript
- Files and data: https://observablehq.com/framework/files
- Inputs: https://observablehq.com/framework/inputs
- Config: https://observablehq.com/framework/config
