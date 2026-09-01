"""
表达式引擎模块

提供安全的表达式解析和执行功能，用于计算字段（computed fields）的值。
支持算术、比较、逻辑运算和数学函数。

使用 simpleeval 库实现安全沙箱，禁用全局对象访问，并添加超时保护。
"""
import ast
import math
import time
import signal
import operator
from typing import Any, Dict, Optional
from simpleeval import simple_eval


class ExpressionError(Exception):
    """表达式执行错误"""
    pass


class ExpressionTimeout(Exception):
    """表达式执行超时"""
    pass


class ExpressionEngine:
    """
    安全的表达式引擎

    支持的操作：
    - 算术运算：+, -, *, /, %, **
    - 比较运算：>, <, >=, <=, ==, !=
    - 逻辑运算：and, or, not
    - 数学函数：round, floor, ceil, abs, toFixed

    安全措施：
    - 禁用全局对象访问（builtins, __import__ 等）
    - 超时保护（防止死循环）
    - 白名单函数和变量
    """

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 5.0

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        初始化表达式引擎

        :param timeout: 表达式执行超时时间（秒），默认 5 秒
        """
        self.timeout = timeout

        # 定义允许的函数白名单
        self._functions = {
            # 基础数学函数
            'round': round,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,

            # 数学模块函数
            'floor': math.floor,
            'ceil': math.ceil,
            'sqrt': math.sqrt,
            'pow': pow,

            # 自定义函数
            'toFixed': self._to_fixed,
        }

        # 定义允许的名称白名单（常量）
        self._names = {
            'true': True,
            'false': False,
            'null': None,
            'True': True,
            'False': False,
            'None': None,
            'pi': math.pi,
            'e': math.e,
        }

        # 定义允许的运算符（使用 AST 节点类型作为 key，simpleeval 的要求）
        self._operators = {
            # 算术运算
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,   # 一元负号
            ast.UAdd: operator.pos,   # 一元正号
            ast.Not: operator.not_,   # 逻辑非

            # 比较运算
            ast.Gt: operator.gt,
            ast.Lt: operator.lt,
            ast.GtE: operator.ge,
            ast.LtE: operator.le,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
        }

    def _to_fixed(self, value: float, digits: int = 2) -> float:
        """
        格式化数字到指定小数位

        :param value: 要格式化的数字
        :param digits: 小数位数，默认 2
        :return: 格式化后的浮点数
        """
        try:
            return round(float(value), int(digits))
        except (ValueError, TypeError) as e:
            raise ExpressionError(f"toFixed 函数参数错误: {e}")

    def evaluate(self, expression: str, variables: Optional[Dict[str, Any]] = None) -> Any:
        """
        计算表达式

        :param expression: 表达式字符串，如 "price * quantity"
        :param variables: 变量字典，如 {"price": 100, "quantity": 5}
        :return: 计算结果
        :raises ExpressionError: 表达式语法错误或执行错误
        :raises ExpressionTimeout: 表达式执行超时
        """
        if not expression or not expression.strip():
            raise ExpressionError("表达式不能为空")

        if variables is None:
            variables = {}

        # 合并变量和白名单名称
        names = {**self._names, **variables}

        # 设置超时保护
        old_handler = None
        try:
            # 使用 signal 实现超时保护（仅在 Unix 系统有效）
            if hasattr(signal, 'SIGALRM'):
                def timeout_handler(signum, frame):
                    raise ExpressionTimeout(f"表达式执行超时（{self.timeout}秒）")

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.timeout))

            try:
                # 使用 simpleeval 安全执行表达式
                result = simple_eval(
                    expression.strip(),
                    functions=self._functions,
                    names=names,
                    operators=self._operators,
                )

                # 恢复信号
                if old_handler is not None:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

                return result

            except ExpressionTimeout:
                raise
            except SyntaxError as e:
                raise ExpressionError(f"表达式语法错误: {e}")
            except NameError as e:
                raise ExpressionError(f"未知变量: {e}")
            except ZeroDivisionError:
                raise ExpressionError("除零错误")
            except Exception as e:
                raise ExpressionError(f"表达式执行错误: {e}")

        finally:
            # 确保恢复信号处理
            if old_handler is not None and hasattr(signal, 'SIGALRM'):
                try:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                except Exception:
                    pass

    def validate(self, expression: str, available_variables: Optional[list] = None) -> bool:
        """
        验证表达式语法是否正确

        :param expression: 表达式字符串
        :param available_variables: 可用变量名列表
        :return: True 如果表达式有效
        :raises ExpressionError: 表达式无效
        """
        if not expression or not expression.strip():
            raise ExpressionError("表达式不能为空")

        try:
            # 创建虚拟变量
            names = {**self._names}
            if available_variables:
                for var in available_variables:
                    names[var] = 0  # 使用 0 作为占位值

            # 尝试执行（使用安全的占位值）
            simple_eval(
                expression.strip(),
                functions=self._functions,
                names=names,
                operators=self._operators,
            )

            return True

        except ExpressionError:
            raise
        except Exception as e:
            raise ExpressionError(f"表达式验证失败: {e}")

    def get_supported_functions(self) -> list:
        """
        获取支持的函数列表

        :return: 函数名列表
        """
        return list(self._functions.keys())


# 全局实例（单例模式）
_engine_instance: Optional[ExpressionEngine] = None


def get_expression_engine(timeout: float = ExpressionEngine.DEFAULT_TIMEOUT) -> ExpressionEngine:
    """
    获取表达式引擎实例（单例）

    :param timeout: 超时时间（秒）
    :return: ExpressionEngine 实例
    """
    global _engine_instance
    if _engine_instance is None or _engine_instance.timeout != timeout:
        _engine_instance = ExpressionEngine(timeout=timeout)
    return _engine_instance
