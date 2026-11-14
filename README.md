# Linux C编程一站式学习 · LaTeX 排版整理版

原作者宋劲杉，原出版机构北京亚嵌教育研究中心。工程包含原书 HTML 快照、原图、分章 LaTeX、UTF-8 代码示例和 A4 PDF。原书和本版按 GNU Free Documentation License 1.3 或后续版本提供，不可变章节为「前言」。原书版权、许可证声明和全文见 PDF 版权页和附录 B。

- [原书在线版](https://akaedu.github.io/book/)
- [本地 PDF](output/linux-c-book.pdf)
- [转换与验收报告](conversion-report.md)

## 编译

进入本目录运行 `make pdf`。LaTeX 文件和语法着色数据都已生成，离线编译只需要 XeLaTeX、latexmk、所列 TeX 宏包和字体。编译禁止 shell escape。latexmk 自动完成目录、书签、交叉引用和索引页码所需的多轮构建。

Debian / Ubuntu 可安装以下软件包。

```sh
sudo apt-get install make latexmk texlive-xetex texlive-lang-chinese \
  texlive-latex-extra texlive-fonts-recommended fonts-noto-cjk fonts-dejavu-core
make pdf
```

其他平台可用 TeX Live 或 MacTeX。正常使用 Noto CJK、TeX Gyre 与 DejaVu Sans Mono。中文首先尝试 Noto，缺少时回退到 Fandol，最后尝试 AR PL UMing 与文泉驿微米黑。建议安装 Noto CJK 以获得随附 PDF 的字形。拉丁字体有 Latin Modern 回退。

输出为 `output/linux-c-book.pdf`，日志和其他构建文件在 `output/.build/`。运行 `make clean` 可清除临时编译文件，然后用 `make pdf` 从头构建。

## 工程结构与编辑

| 路径 | 内容 |
| --- | --- |
| `main.tex` | 封面、卷首、三部分、附录及卷末的编排入口 |
| `config/` | 宏包、版式、可填写的版本信息和公共命令 |
| `frontmatter/` | 封面、版权页、修订历史、历史和原书前言 |
| `chapters/part1/` 至 `part3/` | 37 章，每章一个独立的 `.tex` 文件 |
| `appendices/`、`references/`、`index/` | 两个附录、参考书目和原书索引 |
| `code/` | 按原网页分组的完整 UTF-8 示例及语法着色数据 `.pv` |
| `images/` | 原图和 GIF 的等像素 PNG 派生文件 |
| `source-html/` | 原站 HTML 和 CSS 快照 |
| `manifest/source.json` | URL、目录层级、导航、资源路径、SHA-256 与获取失败记录 |
| `manifest/conversion.json` | URL 和节锚点到 TeX 的映射，代码路径与源站失效链接修复记录 |

手工排版可直接修改章节的 `.tex` 文件后运行 `make pdf`。调整全局版式时编辑 `config/settings.tex` 和 `config/commands.tex`。示例的准确复制以 `code/` 中原始文件为准，PDF 上的行号、换行和制表符展开属于显示层。批量修改转换规则后再运行 `make convert`，该命令会重新生成章节和其他派生文件，请先保存手工编辑。原书的「前言」为不可变章节。

从现有快照重新生成需要 Python 3、Pygments 和 Pillow。重新抓取另需要 curl，当前工程已附有完整快照，可以直接离线从 `make images` 开始。

```sh
sudo apt-get install python3 python3-pygments python3-pil curl
make fetch
make images
make convert
make verify
make pdf
```

`make fetch` 会重新下载整站快照并重写来源清单。只有需要刷新快照时才运行。检查和生成命令均从项目目录运行，Makefile 的 `PYTHON` 和 `LATEXMK` 可覆盖。

## 正式发布前填写

在 `config/edition.tex` 填写实际整理者、发布者和本版排版版权人。填写后重编封面、版权页和修订历史。如调整发布日期或版本号，同一文件中也有相应字段。再发布时请保留原作者和版权声明、不可变的「前言」、修订历史、原书链接和 GFDL 全文，并将可编辑的 LaTeX 工程与 PDF 一同分发。GFDL 的修改版本及副本要求见官方许可证第 3、4 条。 [GNU Free Documentation License 1.3](https://www.gnu.org/licenses/fdl-1.3.html)
