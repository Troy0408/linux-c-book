# HTML 结构调查

范围：`source-html/` 中 219 个 HTML，Python 标准库 `html.parser` 逐文件统计，`xml.etree.ElementTree` 核查正文、数学和许可内容。文件为 UTF-8、DocBook XSL 1.73.2 生成的 XHTML 1.0 Transitional；保留原文和锚点。

## 主要结构

每页 `html/head/body`，head 含标题、stylesheet 和导航链接；body 一般由 `div.navheader`、`div.book/part/chapter/sect1/appendix/...` 正文、`div.navfooter` 组成。导航内部也使用 table，而正文 48 个 `div.table` 带表题、`table-contents` 和真实表格，不能按 table 标签批量删除。目录采用 dl/dt/dd；正文有有序/无序列表、标题、段落、图、例子、注释、参考文献与索引。`a.indexterm` 是空锚点；`a.xref`、普通 href 和 id 包含交叉引用。`titlepage` 含多层 div 和标题，勿仅按层级取单一正文。

标签计数：a 4676、code 8283、p 3632、div 3209、span 1555、table 487、pre 1075、img 143、sup 170、sub 145。语义 class：literal 8282、indexterm 1224、programlisting 726、screen 349、figure 137、example 96、footnote 78、footnotes 32、literallayout 69、table 48、note 8。navheader/navfooter 各 219。计数基于 HTML 起始标签，self-closing 标签由解析器同样计数。

`pre.programlisting` 是程序，`pre.screen` 是终端输入输出，空格、Tab、换行及内嵌文本都应原样保留；示例 `ch19s01.html` 的反汇编输出含 Tab 和对齐空格。`div.literallayout` 并非仅公式：包含语法产生式、码表、网络报文、命令、表内文本及 GFDL，须保留空白和 br。图 `div.figure` 有标题、锚点、`img src/alt` 和 figure-break；示例 `ch19s01.html`。脚注正文链接如 `ch19s01.html` 的 `a.footnote` 指向 `#ftn...`，页尾 footnotes 包含返回锚点，需保留关系及编号。

## 数学和边界

未发现 MathML、SVG、script、object、iframe。公式用普通文字、Unicode、`sub/sup`、NBSP、`br` 表示。`ch05s02.html` 两条单行公式为根式和圆面积；`ch14s02.html` 进制展开有上下标；`ch04s03.html` 为多行布尔代数；`ch05s03.html` 为阶乘和 Fibonacci 多行；`expr.expression.html` 有地板/天花板多行。`ch14s02.html` 另有余数标注和原文不平衡括号，`ch14s03.html` 有中文步骤，不能无依据重写。`ch11s04.html`、`ch19s03.html` 中数学和中文混排。`scripts/book_math.py` 只按精确文本白名单转换 6 个明确的单行公式，其他返回 None，且不对源文件作任何变更。`ch05s02` 两式和 `ch14s02` 四式覆盖该白名单。

## 许可核验

`apb.html` 标题在正文容器的标题中，license 内容在 literallayout 中，包含 0–11 全部编号条款和 ADDENDUM，结尾完整。与系统 `/usr/share/doc/texlive-doc/dvipdfmx/fdl-1.3.txt.gz` 提取文本、规范空白后逐字符比较：差异为标题位置、© 与 (C)、第 4 条 A–O 前的星号、破折号、示例版权符号大小写、末尾示例省略号字形；未发现条款缺失或正文截断。保留原站标题与全文，不需补条款。

## 验证方法

用 `pathlib.Path.glob('*.html')` 和 `html.parser.HTMLParser` 累计标签及 class；用 XML 解析器提取 literallayout、遍历 sub/sup；用 gzip 解压本机 GFDL，合并空白后以 `difflib.SequenceMatcher(autojunk=False)` 审查所有差异。原始 HTML 未修改。
