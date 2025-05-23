"""Test Jac cli module."""

import contextlib
import inspect
import io
import os
import subprocess
import sys
import traceback

from jaclang.cli import cli
from jaclang.runtimelib.builtin import dotgen
from jaclang.utils.test import TestCase


class JacCliTests(TestCase):
    """Test pass module."""

    def setUp(self) -> None:
        """Set up test."""
        return super().setUp()

    def test_jac_cli_run(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Execute the function
        cli.run(self.fixture_abs_path("hello.jac"))

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()

        self.assertIn("Hello World!", stdout_value)

    def test_jac_cli_alert_based_err(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output

        try:
            cli.enter(self.fixture_abs_path("err2.jac"), entrypoint="speak", args=[])
        except Exception as e:
            print(f"Error: {e}")

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        stdout_value = captured_output.getvalue()
        # print(stdout_value)
        self.assertIn("Error", stdout_value)

    def test_jac_cli_alert_based_runtime_err(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output

        with contextlib.suppress(Exception):
            cli.run(self.fixture_abs_path("err_runtime.jac"))

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        expected_stdout_values = (
            "Error: list index out of range",
            "    print(some_list[invalid_index]);",
            "          ^^^^^^^^^^^^^^^^^^^^^^^^",
            "  at bar() ",
            "  at foo() ",
            "  at <module> ",
        )
        logger_capture = "\n".join([rec.message for rec in self.caplog.records])
        for exp in expected_stdout_values:
            self.assertIn(exp, logger_capture)

    def test_jac_impl_err(self) -> None:
        """Basic test for pass."""
        if "jaclang.tests.fixtures.err" in sys.modules:
            del sys.modules["jaclang.tests.fixtures.err"]
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output

        try:
            cli.enter(self.fixture_abs_path("err.jac"), entrypoint="speak", args=[])
        except Exception:
            traceback.print_exc()

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        stdout_value = captured_output.getvalue()
        # print(stdout_value)
        path_to_file = self.fixture_abs_path("err.impl.jac")
        self.assertIn(f'"{path_to_file}", line 2', stdout_value)

    def test_param_name_diff(self) -> None:
        """Test when parameter name from definitinon and declaration are mismatched."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output
        with contextlib.suppress(Exception):
            cli.run(self.fixture_abs_path("decl_defn_param_name.jac"))
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        expected_stdout_values = (
            "short_name = 42",
            "p1 = 64 , p2 = foobar",
        )
        output = captured_output.getvalue()
        for exp in expected_stdout_values:
            self.assertIn(exp, output)

    def test_jac_test_err(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output
        cli.test(self.fixture_abs_path("baddy.jac"))
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        stdout_value = captured_output.getvalue()
        path_to_file = self.fixture_abs_path("baddy.test.jac")
        self.assertIn(f'"{path_to_file}", line 2,', stdout_value)

    def test_jac_ast_tool_pass_template(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("pass_template")

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("Sub objects.", stdout_value)
        self.assertGreater(stdout_value.count("def exit_"), 10)

    def test_jac_cmd_line(self) -> None:
        """Basic test for pass."""
        process = subprocess.Popen(
            ["jac"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout_value, _ = process.communicate(input="exit\n")
        self.assertEqual(process.returncode, 0, "Process did not exit successfully")
        self.assertIn("Welcome to the Jac CLI!", stdout_value)

    def test_ast_print(self) -> None:
        """Testing for print AstTool."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast", f"{self.fixture_abs_path('hello.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("+-- Token", stdout_value)

    def test_import_mod_abs_path(self) -> None:
        """Testing for print AstTool."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast", f"{self.fixture_abs_path('import.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue().replace("\\", "/")
        self.assertRegex(
            stdout_value,
            r"1\:11 \- 1\:13.*ModulePath - os - abs_path\:.*typeshed/stdlib/os/__init__.pyi",
        )
        self.assertRegex(
            stdout_value,
            r"2\:11 \- 2\:14.*ModulePath - sys - abs_path\:.*typeshed/stdlib/sys/__init__.pyi",
        )
        self.assertRegex(
            stdout_value,
            r"3\:11 \- 3\:17.*ModulePath - pyfunc - abs_path\:.*fixtures/pyfunc.py",
        )
        self.assertRegex(
            stdout_value,
            r"4\:11 \- 4\:28.*ModulePath - pygame_mock - abs_path\:.*fixtures/pygame_mock/inner/__init__.py",
        )
        self.assertRegex(
            stdout_value,
            r"6\:11 \- 6\:15.*ModulePath - math - abs_path\:.*typeshed/stdlib/math.pyi",
        )
        self.assertRegex(
            stdout_value,
            r"7\:11 \- 7\:19.*ModulePath - argparse - abs_path\:.*typeshed/stdlib/argparse.pyi",
        )
        self.assertRegex(
            stdout_value,
            r"8\:16 \- 8\:27.*ModulePath - pygame_mock - abs_path\:.*fixtures/pygame_mock/__init__.py",
        )
        self.assertRegex(
            stdout_value,
            r"8\:30 \- 8:35.*ModuleItem - color - abs_path\:.*fixtures/pygame_mock/color.py",
        )
        self.assertRegex(
            stdout_value,
            r"8\:37 \- 8:44.*ModuleItem - display - abs_path\:.*fixtures/pygame_mock/display.py",
        )

    def test_builtins_loading(self) -> None:
        """Testing for print AstTool."""
        from jaclang.settings import settings

        settings.ast_symbol_info_detailed = True
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast", f"{self.fixture_abs_path('builtins_test.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        settings.ast_symbol_info_detailed = False

        self.assertRegex(
            stdout_value,
            r"2\:8 \- 2\:12.*BuiltinType - list - .*SymbolPath: builtins.list",
        )
        self.assertRegex(
            stdout_value,
            r"15\:5 \- 15\:8.*Name - dir - .*SymbolPath: builtins.dir",
        )
        self.assertRegex(
            stdout_value,
            r"13\:12 \- 13\:18.*Name - append - .*SymbolPath: builtins.list.append",
        )

    def test_import_all(self) -> None:
        """Testing for print AstTool."""
        from jaclang.settings import settings

        settings.ast_symbol_info_detailed = True
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast", f"{self.fixture_abs_path('import_all.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        settings.ast_symbol_info_detailed = False

        self.assertRegex(
            stdout_value,
            r"6\:25 - 6\:30.*Name - floor -.*SymbolPath: math.floor",
        )
        self.assertRegex(
            stdout_value,
            r"5\:25 - 5\:27.*Name - pi -.*SymbolPath: math.pi",
        )

    def test_sub_class_symbol_table_fix_1(self) -> None:
        """Testing for print AstTool."""
        from jaclang.settings import settings

        settings.ast_symbol_info_detailed = True
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast", f"{self.fixture_abs_path('base_class1.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        settings.ast_symbol_info_detailed = False

        self.assertRegex(
            stdout_value,
            r"10:7 - 10:12.*Name - start - Type.*SymbolPath: base_class1.B.start",
        )

    def test_sub_class_symbol_table_fix_2(self) -> None:
        """Testing for print AstTool."""
        from jaclang.settings import settings

        settings.ast_symbol_info_detailed = True
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast", f"{self.fixture_abs_path('base_class2.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        settings.ast_symbol_info_detailed = False

        self.assertRegex(
            stdout_value,
            r"10:7 - 10:12.*Name - start - Type.*SymbolPath: base_class2.B.start",
        )

    def test_base_class_complex_expr(self) -> None:
        """Testing for print AstTool."""
        from jaclang.settings import settings

        # settings.ast_symbol_info_detailed = True
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool(
            "ir", ["ast", f"{self.fixture_abs_path('base_class_complex_expr.jac')}"]
        )

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        settings.ast_symbol_info_detailed = False

        self.assertRegex(
            stdout_value,
            r"36\:9 \- 36\:13.*Name \- Kiwi \- Type\: base_class_complex_expr.Kiwi,  SymbolTable\: Kiwi",
        )

    def test_expr_types(self) -> None:
        """Testing for print AstTool."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast", f"{self.fixture_abs_path('expr_type.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()

        self.assertRegex(
            stdout_value, r"4\:9 \- 4\:14.*BinaryExpr \- Type\: builtins.int"
        )
        self.assertRegex(
            stdout_value, r"7\:9 \- 7\:17.*FuncCall \- Type\: builtins.float"
        )
        self.assertRegex(
            stdout_value, r"9\:6 \- 9\:11.*CompareExpr \- Type\: builtins.bool"
        )
        self.assertRegex(
            stdout_value, r"10\:6 - 10\:15.*BinaryExpr \- Type\: builtins.str"
        )
        self.assertRegex(
            stdout_value, r"11\:5 \- 11\:13.*AtomTrailer \- Type\: builtins.int"
        )
        self.assertRegex(
            stdout_value, r"12\:5 \- 12\:14.*UnaryExpr \- Type\: builtins.bool"
        )
        self.assertRegex(
            stdout_value, r"13\:5 \- 13\:25.*IfElseExpr \- Type\: Literal\['a']\?"
        )
        self.assertRegex(
            stdout_value,
            r"14\:5 \- 14\:27.*ListCompr - \[ListCompr] \- Type\: builtins.list\[builtins.int]",
        )

    def test_ast_dotgen(self) -> None:
        """Testing for print AstTool."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        cli.tool("ir", ["ast.", f"{self.fixture_abs_path('hello.jac')}"])

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn(
            '[label="MultiString" shape="oval" style="filled" fillcolor="#fccca4"]',
            stdout_value,
        )

    def test_type_check(self) -> None:
        """Testing for print AstTool."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        cli.check(f"{self.fixture_abs_path('game1.jac')}")
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("Errors: 0, Warnings: 2", stdout_value)

    def test_type_info(self) -> None:
        """Testing for type info inside the ast tool."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        cli.tool("ir", ["ast", f"{self.fixture_abs_path('type_info.jac')}"])
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.count("type_info.ServerWrapper"), 7)
        self.assertEqual(stdout_value.count("builtins.int"), 3)
        self.assertEqual(stdout_value.count("builtins.str"), 10)
        self.assertIn("Literal['test_server']", stdout_value)
        self.assertIn("Literal['1']", stdout_value)

    def test_build_and_run(self) -> None:
        """Testing for print AstTool."""
        if os.path.exists(f"{self.fixture_abs_path('needs_import.jir')}"):
            os.remove(f"{self.fixture_abs_path('needs_import.jir')}")
        captured_output = io.StringIO()
        sys.stdout = captured_output
        cli.build(f"{self.fixture_abs_path('needs_import.jac')}")
        cli.run(f"{self.fixture_abs_path('needs_import.jir')}")
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        print(stdout_value)
        self.assertIn("Errors: 0, Warnings: 0", stdout_value)
        self.assertIn("<module 'pyfunc' from", stdout_value)

    def test_cache_no_cache_on_run(self) -> None:
        """Basic test for pass."""
        process = subprocess.Popen(
            ["jac", "run", f"{self.fixture_abs_path('hello_nc.jac')}", "-nc"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, _ = process.communicate()
        self.assertFalse(
            os.path.exists(
                f"{self.fixture_abs_path(os.path.join('__jac_gen__', 'hello_nc.jbc'))}"
            )
        )
        self.assertIn("Hello World!", stdout)
        process = subprocess.Popen(
            ["jac", "run", f"{self.fixture_abs_path('hello_nc.jac')}", "-c"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, _ = process.communicate()
        self.assertIn("Hello World!", stdout)

    def test_run_test(self) -> None:
        """Basic test for pass."""
        process = subprocess.Popen(
            ["jac", "test", f"{self.fixture_abs_path('run_test.jac')}", "-m 2"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        self.assertIn("Ran 3 tests", stderr)
        self.assertIn("FAILED (failures=2)", stderr)
        self.assertIn("F.F", stderr)

        process = subprocess.Popen(
            [
                "jac",
                "test",
                "-d" + f"{self.fixture_abs_path('../../../')}",
                "-f" + "circle*",
                "-x",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        self.assertIn("circle", stdout)
        self.assertNotIn("circle_purfe.test", stdout)
        self.assertNotIn("circle_pure.impl", stdout)

        process = subprocess.Popen(
            ["jac", "test", "-f" + "*run_test.jac", "-m 3"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        self.assertIn("...F", stderr)
        self.assertIn("F.F", stderr)

    def test_run_specific_test_only(self) -> None:
        """Test a specific test case."""
        process = subprocess.Popen(
            [
                "jac",
                "test",
                "-t",
                "from_2_to_10",
                self.fixture_abs_path("jactest_main.jac"),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        self.assertIn("Ran 1 test", stderr)
        self.assertIn("Testing fibonacci numbers from 2 to 10.", stdout)
        self.assertNotIn("Testing first 2 fibonacci numbers.", stdout)
        self.assertNotIn("This test should not run after import.", stdout)

    def test_graph_coverage(self) -> None:
        """Test for coverage of graph cmd."""
        graph_params = set(inspect.signature(cli.dot).parameters.keys())
        dotgen_params = set(inspect.signature(dotgen).parameters.keys())
        dotgen_params = dotgen_params - {"node", "dot_file", "edge_type"}
        dotgen_params.update({"initial", "saveto", "connection", "session"})
        self.assertTrue(dotgen_params.issubset(graph_params))
        self.assertEqual(len(dotgen_params) + 1, len(graph_params))

    def test_graph(self) -> None:
        """Test for graph CLI cmd."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        cli.dot(f"{self.examples_abs_path('reference/connect_expressions.jac')}")
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        if os.path.exists("connect_expressions.dot"):
            os.remove("connect_expressions.dot")
        self.assertIn("11\n13\n15\n>>> Graph content saved to", stdout_value)
        self.assertIn("connect_expressions.dot\n", stdout_value)

    def test_py_to_jac(self) -> None:
        """Test for graph CLI cmd."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        cli.py2jac(f"{self.fixture_abs_path('../../tests/fixtures/pyfunc.py')}")
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("can my_print(x: object) -> None", stdout_value)

    def test_caching_issue(self) -> None:
        """Test for Caching Issue."""
        test_file = self.fixture_abs_path("test_caching_issue.jac")
        test_cases = [(10, True), (11, False)]
        for x, is_passed in test_cases:
            with open(test_file, "w") as f:
                f.write(
                    f"""
                test mytest{{
                    check 10 == {x};
                }}
                """
                )
            process = subprocess.Popen(
                ["jac", "test", test_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()
            if is_passed:
                self.assertIn("Passed successfully.", stdout)
                self.assertIn(".", stderr)
            else:
                self.assertNotIn("Passed successfully.", stdout)
                self.assertIn("F", stderr)
        os.remove(test_file)
