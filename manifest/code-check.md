# 代码与 PDF 核查

核查范围：219 个本地 XHTML，1075 个 `pre`（726 `programlisting`、349 `screen`）。以（页面名、原文）多重集合比较 `ElementTree` 的 `''.join(pre.itertext())` 与 conversion.json 记录的 UTF-8 源文件：缺失 0、额外 0；所有 SHA-256 一致。每块的渲染文件在生成 TeX 中恰好引用一次，语种提示与 `book_code.language` 一致。88 块含非 ASCII，405 块含制表符。ch31s01 的四块由于呈现顺序变化，其编号不同于原 HTML 的先后顺序，但内容均存在；不能依赖序号建立源节点映射。

静态检查：Pygments 使用 `get_tokens_unprocessed` 并校验令牌回拼；`LatexFormatter(commandprefix='BK', nowrap=True, style='friendly', nobackground=True)`，配合 `VerbatimPygments`，排版中使用 `breaklines`、`breakanywhere`、`obeytabs` 和 `tabsize=8`。生成源码提供用于准确复制的原始 UTF-8 文件。自动换行和 PDF 文本布局不能保证原始空白与原文件字节一致。

`pdftotext -layout output/linux-c-book.pdf /tmp/book-qa.txt` 检查 645 页 PDF：C 的 `int main(void)` 和 `printf("Hello, world.\\n");`、终端 `$ gcc main.c`、Make 的 `main: main.o stack.o maze.o`、汇编 `.globl _start` 及反汇编 `%ebp` 可找到；`if (临时变量) { /* 临时变量用完就释放 */` 中文注释可提取。单行提取保留了这些样本的行边界，PDF 添加的缩进和行号不等于源码中的原始空白；该抽样不能证明所有代码行的视觉断行均符合预期。构建日志中未检出 `Missing character`，存在少量 overfull 警告，需要结合上下文另行排版检查。

检查方式：Python 标准库 ElementTree、Counter 按页面与文本比较，逐块读取 UTF-8 并验证 sha256、TeX 引用和语言提示；`pdfinfo`、`pdftotext -layout`、`rg` 抽样和日志搜索。以上结果针对本次构建快照。
