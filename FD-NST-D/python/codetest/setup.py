# setup.py
from setuptools import setup
from Cython.Build import cythonize

setup(
    name="My Protected App",
    ext_modules=cythonize(
        "FD_NST_D.pyx",   # 指定要编译的 .pyx 文件
        # 可选：编译选项，以下配置使输出更难以反编译
        compiler_directives={
            'language_level': "3",    # 使用 Python 3 语法
            'cdivision': True,        # 启用 C 风格的除法，提高安全性/性能
            'boundscheck': False,     # 禁用边界检查，提高安全性/性能
            'wraparound': False,      # 禁用负数索引包装，提高安全性/性能
            # 'nonecheck': False,     # 禁用空值检查
        },
        # 可选：开启深度混淆，使生成的 C 代码难以阅读
        # annotate=True 会生成一个.html文件，显示哪些代码是纯Python的（黄色），哪些被转换成了C（白色）。用于优化，而非发布。
        # annotate=True
    ),
    # 可选：要求 zip 包含已编译的模块，增加提取难度
    zip_safe=False,
)