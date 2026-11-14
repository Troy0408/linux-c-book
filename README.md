# Linux C 编程一站式学习 · LaTeX 排版整理版

[![License: GFDL 1.3](https://img.shields.io/badge/License-GFDL%201.3-blue.svg)](https://www.gnu.org/licenses/fdl-1.3.html)
[![Engine: XeLaTeX](https://img.shields.io/badge/Built%20with-XeLaTeX-008080.svg)](#编译)
[![Pages: 692 A4](https://img.shields.io/badge/PDF-692%20Pages%20A4-brightgreen.svg)](output/linux-c-book.pdf)

经典开源教材《Linux C 编程一站式学习》（原作者 **宋劲杉**，原出版机构 **北京亚嵌教育研究中心**）的 **LaTeX 精排开源电子书工程**。仓库包含可直接阅读的 692 页 A4 PDF、完整可编译的 XeLaTeX 源码、原站 HTML/CSS 快照、全量原图与可直接复制运行的 UTF-8 代码示例。

- **直接阅读 / 下载 PDF**：[output/linux-c-book.pdf](output/linux-c-book.pdf)
- **原书在线版**：[akaedu.github.io/book](https://akaedu.github.io/book/)
- **转换与验收报告**：[conversion-report.md](conversion-report.md)

---

## 排版与整理特色

- **出版级中文技术书版式**：基于 `ctexbook` + XeLaTeX 排版（Noto CJK / TeX Gyre Pagella / DejaVu Sans Mono），行距舒展、中英文混排间距自然。
- **完整超链接与检索体系**：支持 PDF 书签、可点击章节目录、文内交叉引用跳转（含 279 处原站失效片段修复）、628 条可回跳术语索引，以及 137 张插图、48 张三线表、96 个示例与 39 条脚注。
- **代码与表格精细优化**：
  - 726 段程序清单与 349 段终端输出支持 Pygments 语法着色、行号显示与自动折行，`code/` 目录同步提供原始 UTF-8 源码便于精确复制。
  - 全部 48 张表格采用自适应列宽并居中展示；定义列表、插图/公式比例与例题/章节防孤立分页均经全书通检优化。
- **离线一致性校验**：提供 `scripts/verify.py` 自动化校验 HTML 快照完整性、目录结构、图表/示例计数、图片路径、不可变章节「前言」与 GFDL 许可证全文。

---

## 全书内容结构

| 部分 | 内容范围 | 涵盖章节 |
| --- | --- | --- |
| 卷首 | 封面、版权及许可证声明、修订历史、历史、前言（不可变章节）、目录 | — |
| 第一部分 | **C 语言入门** | 第 1–13 章 |
| 第二部分 | **C 语言本质** | 第 14–27 章 |
| 第三部分 | **Linux 系统编程** | 第 28–37 章 |
| 附录与卷末 | 附录 A（字符编码）、附录 B（GFDL 1.3 全文）、参考书目、索引 | — |

全书共 **3 部分、37 章、172 节、124 个编号子节、64 个非编号小节**。

---

## 编译

仓库已生成全部 LaTeX 章节与语法着色数据，离线编译只需要 XeLaTeX、`latexmk` 与对应字体（编译禁用 shell escape）：

```sh
# Debian / Ubuntu 安装依赖
sudo apt-get install make latexmk texlive-xetex texlive-lang-chinese \
  texlive-latex-extra texlive-fonts-recommended fonts-noto-cjk fonts-dejavu-core

# 编译生成 output/linux-c-book.pdf
make pdf
```

> 建议使用 Noto CJK、TeX Gyre 与 DejaVu Sans Mono 字体以获得与随附 PDF 一致的字形效果；缺少 Noto 时会自动回退到 Fandol / AR PL UMing / 文泉驿微米黑等字体，拉丁字体回退到 Latin Modern。

输出 PDF 位于 `output/linux-c-book.pdf`，中间构建文件保存在 `output/.build/`。运行 `make clean` 可清除临时构建文件后重新编译。

### 从快照重新生成

如需修改转换规则并重新生成全部 `.tex` 章节（需要 Python 3、Pygments 和 Pillow；工程已自带完整快照，无需联网抓取）：

```sh
sudo apt-get install python3 python3-pygments python3-pil
make images    # 派生图片处理
make convert   # HTML -> TeX 转换
make verify    # 离线完整性与一致性校验
make pdf       # 编译生成 PDF
```

- 如仅局部微调版式，可直接修改 `config/settings.tex`、`config/commands.tex` 或对应章节 `.tex` 后运行 `make pdf`（注意运行 `make convert` 会重新覆盖派生 `.tex` 文件）。
- 仅在需要重新抓取原站网页时才运行 `make fetch`（需安装 `curl`）。可通过覆盖 Makefile 的 `PYTHON` 与 `LATEXMK` 变量指定自定义工具链路径。

---

## 工程结构

| 路径 | 说明 |
| --- | --- |
| `main.tex` | 封面、卷首、三部分、附录及卷末编排入口 |
| `config/` | 宏包配置、全局版式样式、版本信息（`edition.tex`）与公共命令 |
| `frontmatter/` | 封面、版权页、修订历史、历史和原书前言 |
| `chapters/part1/` – `part3/` | 37 章独立 `.tex` 源码 |
| `appendices/`、`references/`、`index/` | 附录 A/B、参考书目与术语索引 |
| `code/` | 按原网页分组的完整 UTF-8 代码示例及 Pygments 着色数据 `.pv` |
| `images/` | 原图及 GIF 的等像素 PNG 派生文件 |
| `source-html/` | 原站 XHTML 与 CSS 离线快照 |
| `scripts/` | 抓取、图片处理、HTML→LaTeX 转换、表格排版与完整性校验脚本 |
| `manifest/` | URL 映射、SHA-256 清单及离线验收记录 |
| `output/` | 最终发布的 A4 PDF（`linux-c-book.pdf`） |

---

## 版权与许可证

- 原书及本整理版均依据 **GNU Free Documentation License Version 1.3** 或自由软件基金会发布的任何后续版本分发。
- 本版完整保留原作者（宋劲杉 / 北京亚嵌教育研究中心）版权声明、不可变章节「前言」（无 Front-Cover Texts 与 Back-Cover Texts）、历史与修订历史、原书网址，以及完整可编辑的 LaTeX 源码工程。
- 许可证全文见 [PDF 附录 B](output/linux-c-book.pdf) 或 [GNU Free Documentation License 1.3](https://www.gnu.org/licenses/fdl-1.3.html)。
