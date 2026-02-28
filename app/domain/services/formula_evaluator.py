"""Formula evaluator service for computed columns."""

import re
import operator
from typing import Any, Callable


class FormulaEvaluatorService:
    """Service for evaluating formula expressions in computed columns.

    Supports:
    - Basic arithmetic: +, -, *, /
    - Column references: {column_name}
    - String concatenation: CONCAT(col1, col2, "literal")
    - Numeric functions: SUM, AVG, MIN, MAX
    - String functions: UPPER, LOWER, TRIM, LENGTH
    - Conditional: IF(condition, then_value, else_value)
    """

    # Operators with their precedence and functions
    _OPERATORS: dict[str, tuple[int, Callable]] = {
        "+": (1, operator.add),
        "-": (1, operator.sub),
        "*": (2, operator.mul),
        "/": (2, operator.truediv),
    }

    # Pattern to find column references: {column_name}
    _COLUMN_REF_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    # Pattern to find function calls: FUNC(args)
    _FUNCTION_PATTERN = re.compile(
        r"([A-Z]+)\s*\(([^)]*)\)",
        re.IGNORECASE,
    )

    def evaluate(
        self,
        formula: str,
        row_data: dict[str, Any],
    ) -> Any:
        """Evaluate a formula expression for a row.

        Args:
            formula: The formula expression
            row_data: Current row's data

        Returns:
            Computed value

        Raises:
            ValueError: If formula is invalid or references unknown columns
        """
        # First, handle function calls
        formula = self._evaluate_functions(formula, row_data)

        # Replace column references with values
        formula = self._substitute_columns(formula, row_data)

        # Evaluate the expression
        return self._evaluate_expression(formula)

    def _substitute_columns(self, formula: str, row_data: dict[str, Any]) -> str:
        """Replace {column_name} with actual values."""

        def replace_column(match: re.Match) -> str:
            column_name = match.group(1)
            if column_name not in row_data:
                raise ValueError(f"Unknown column: {column_name}")

            value = row_data[column_name]
            if value is None:
                return "0"  # Treat null as 0 for numeric operations
            if isinstance(value, str):
                # Escape quotes in strings
                return f'"{value}"'
            return str(value)

        return self._COLUMN_REF_PATTERN.sub(replace_column, formula)

    def _evaluate_functions(self, formula: str, row_data: dict[str, Any]) -> str:
        """Evaluate function calls in the formula."""

        def eval_func(match: re.Match) -> str:
            func_name = match.group(1).upper()
            args_str = match.group(2)

            # Parse arguments
            args = self._parse_args(args_str, row_data)

            # Evaluate function
            result = self._call_function(func_name, args)

            # Return result as string
            if isinstance(result, str):
                return f'"{result}"'
            return str(result)

        # Keep evaluating until no more functions
        prev_formula = None
        while prev_formula != formula:
            prev_formula = formula
            formula = self._FUNCTION_PATTERN.sub(eval_func, formula)

        return formula

    def _parse_args(
        self,
        args_str: str,
        row_data: dict[str, Any],
    ) -> list[Any]:
        """Parse function arguments."""
        if not args_str.strip():
            return []

        args = []
        current_arg = ""
        paren_depth = 0
        in_string = False
        string_char = None

        for char in args_str:
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
                current_arg += char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
                current_arg += char
            elif char == "(" and not in_string:
                paren_depth += 1
                current_arg += char
            elif char == ")" and not in_string:
                paren_depth -= 1
                current_arg += char
            elif char == "," and paren_depth == 0 and not in_string:
                args.append(self._parse_single_arg(current_arg.strip(), row_data))
                current_arg = ""
            else:
                current_arg += char

        if current_arg.strip():
            args.append(self._parse_single_arg(current_arg.strip(), row_data))

        return args

    def _parse_single_arg(self, arg: str, row_data: dict[str, Any]) -> Any:
        """Parse a single argument value."""
        arg = arg.strip()

        # String literal
        if (arg.startswith('"') and arg.endswith('"')) or (
            arg.startswith("'") and arg.endswith("'")
        ):
            return arg[1:-1]

        # Column reference
        if arg.startswith("{") and arg.endswith("}"):
            col_name = arg[1:-1]
            if col_name in row_data:
                return row_data[col_name]
            raise ValueError(f"Unknown column: {col_name}")

        # Number
        try:
            if "." in arg:
                return float(arg)
            return int(arg)
        except ValueError:
            pass

        # Could be a column name without braces
        if arg in row_data:
            return row_data[arg]

        return arg

    def _call_function(self, func_name: str, args: list[Any]) -> Any:
        """Execute a function with arguments."""
        # String functions
        if func_name == "CONCAT":
            return "".join(str(a) for a in args)

        if func_name == "UPPER":
            if args:
                return str(args[0]).upper()
            return ""

        if func_name == "LOWER":
            if args:
                return str(args[0]).lower()
            return ""

        if func_name == "TRIM":
            if args:
                return str(args[0]).strip()
            return ""

        if func_name == "LENGTH":
            if args:
                return len(str(args[0]))
            return 0

        # Numeric functions
        numeric_args = [float(a) for a in args if a is not None]

        if func_name == "SUM":
            return sum(numeric_args)

        if func_name == "AVG":
            if numeric_args:
                return sum(numeric_args) / len(numeric_args)
            return 0

        if func_name == "MIN":
            if numeric_args:
                return min(numeric_args)
            return 0

        if func_name == "MAX":
            if numeric_args:
                return max(numeric_args)
            return 0

        if func_name == "ABS":
            if numeric_args:
                return abs(numeric_args[0])
            return 0

        if func_name == "ROUND":
            if len(numeric_args) >= 1:
                decimals = int(numeric_args[1]) if len(numeric_args) > 1 else 0
                return round(numeric_args[0], decimals)
            return 0

        # Conditional
        if func_name == "IF":
            if len(args) >= 3:
                condition = args[0]
                then_value = args[1]
                else_value = args[2]
                return then_value if condition else else_value
            return None

        # Current date/time
        if func_name == "NOW":
            from datetime import datetime
            return datetime.utcnow().isoformat()

        if func_name == "TODAY":
            from datetime import date
            return date.today().isoformat()

        raise ValueError(f"Unknown function: {func_name}")

    def _evaluate_expression(self, expr: str) -> Any:
        """Evaluate a mathematical expression.

        Simple expression evaluator supporting +, -, *, / and parentheses.
        """
        expr = expr.strip()

        # If it's a string literal, return it
        if (expr.startswith('"') and expr.endswith('"')) or (
            expr.startswith("'") and expr.endswith("'")
        ):
            return expr[1:-1]

        # Try to parse as number directly
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Handle parentheses
        while "(" in expr:
            # Find innermost parentheses
            match = re.search(r"\(([^()]+)\)", expr)
            if not match:
                break
            inner_result = self._evaluate_expression(match.group(1))
            expr = expr[: match.start()] + str(inner_result) + expr[match.end() :]

        # Parse and evaluate
        return self._evaluate_simple_expr(expr)

    def _evaluate_simple_expr(self, expr: str) -> Any:
        """Evaluate expression without parentheses."""
        expr = expr.strip()

        # Try direct number parsing
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Tokenize
        tokens = self._tokenize(expr)

        if not tokens:
            return 0

        # Simple left-to-right evaluation respecting operator precedence
        # First handle * and /
        i = 0
        while i < len(tokens):
            if tokens[i] in ("*", "/"):
                left = float(tokens[i - 1])
                right = float(tokens[i + 1])
                if tokens[i] == "*":
                    result = left * right
                else:
                    result = left / right if right != 0 else 0
                tokens = tokens[: i - 1] + [str(result)] + tokens[i + 2 :]
            else:
                i += 1

        # Then handle + and -
        i = 0
        while i < len(tokens):
            if tokens[i] in ("+", "-"):
                left = float(tokens[i - 1])
                right = float(tokens[i + 1])
                if tokens[i] == "+":
                    result = left + right
                else:
                    result = left - right
                tokens = tokens[: i - 1] + [str(result)] + tokens[i + 2 :]
            else:
                i += 1

        if tokens:
            result = tokens[0]
            try:
                if "." in result:
                    return float(result)
                return int(float(result))
            except (ValueError, TypeError):
                return result

        return 0

    def _tokenize(self, expr: str) -> list[str]:
        """Tokenize an expression into numbers and operators."""
        tokens = []
        current = ""

        for char in expr:
            if char in "+-*/":
                if current.strip():
                    tokens.append(current.strip())
                tokens.append(char)
                current = ""
            elif char.isspace():
                if current.strip():
                    tokens.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            tokens.append(current.strip())

        return tokens

    def get_referenced_columns(self, formula: str) -> list[str]:
        """Get list of columns referenced in a formula.

        Args:
            formula: The formula expression

        Returns:
            List of column names
        """
        matches = self._COLUMN_REF_PATTERN.findall(formula)
        return list(set(matches))
