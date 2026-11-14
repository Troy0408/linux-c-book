"""Conservative conversions of selected single-line textbook formulas."""

_FORMULAS = {
    'distance = √((x_{2}-x_{1})^{2}+(y_{2}-y_{1})^{2})':
        r'\mathrm{distance}=\sqrt{(x_{2}-x_{1})^{2}+(y_{2}-y_{1})^{2}}',
    'area = π·radius^{2}': r'\mathrm{area}=\pi\cdot\mathrm{radius}^{2}',
    '123=1×10^{2}+2×10^{1}+3×10^{0}': r'123=1\times10^{2}+2\times10^{1}+3\times10^{0}',
    '(A_{3}A_{2}A_{1}A_{0})_{2}=A_{3}×2^{3}+A_{2}×2^{2}+A_{1}×2^{1}+A_{0}×2^{0}':
        r'(A_{3}A_{2}A_{1}A_{0})_{2}=A_{3}\times2^{3}+A_{2}\times2^{2}+A_{1}\times2^{1}+A_{0}\times2^{0}',
    '13=1×2^{3}+1×2^{2}+0×2^{1}+1×2^{0}': r'13=1\times2^{3}+1\times2^{2}+0\times2^{1}+1\times2^{0}',
    '(0.A_{1}A_{2}A_{3}...)_{2}=A_{1}×2^{-1}+A_{2}×2^{-2}+A_{3}×2^{-3}+...':
        r'(0.A_{1}A_{2}A_{3}\ldots)_{2}=A_{1}\times2^{-1}+A_{2}\times2^{-2}+A_{3}\times2^{-3}+\ldots',
}


def display_math(text: str) -> str | None:
    """Return math-mode TeX for an exact known formula, otherwise None."""
    return _FORMULAS.get(text.replace('\N{NO-BREAK SPACE}', ' ').strip())
