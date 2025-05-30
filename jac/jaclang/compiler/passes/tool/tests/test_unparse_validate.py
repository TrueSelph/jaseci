"""Test ast build pass module."""

import ast as ast3
from difflib import unified_diff


from jaclang.compiler.passes.main import PyastGenPass
from jaclang.compiler.passes.main.schedules import py_code_gen as without_format
from jaclang.compiler.passes.tool import JacFormatPass
from jaclang.compiler.program import JacProgram
from jaclang.utils.test import AstSyncTestMixin, TestCaseMicroSuite


class JacUnparseTests(TestCaseMicroSuite, AstSyncTestMixin):
    """Test pass module."""

    TargetPass = JacFormatPass

    def test_double_unparse(self) -> None:
        """Parse micro jac file."""
        try:
            code_gen_pure = JacProgram().jac_file_to_pass(
                self.examples_abs_path("manual_code/circle.jac"),
                target=PyastGenPass,
                schedule=without_format,
            )
            x = code_gen_pure.ir_out.unparse()
            y = code_gen_pure.ir_out.unparse()
            self.assertEqual(x, y)
        except Exception as e:
            print("\n".join(unified_diff(x.splitlines(), y.splitlines())))
            raise e

    def micro_suite_test(self, filename: str) -> None:
        """Parse micro jac file."""
        code_gen_pure = JacProgram().jac_file_to_pass(
            self.fixture_abs_path(filename),
            target=PyastGenPass,
            schedule=without_format,
        )
        before = ast3.dump(code_gen_pure.ir_out.gen.py_ast[0], indent=2)
        x = code_gen_pure.ir_out.unparse()
        # print(x)
        # print(f"Testing {code_gen_pure.ir.name}")
        # print(code_gen_pure.ir.pp())
        code_gen_jac = JacProgram().jac_str_to_pass(
            jac_str=x,
            file_path=filename,
            target=PyastGenPass,
            schedule=without_format,
        )
        after = ast3.dump(code_gen_jac.ir_out.gen.py_ast[0], indent=2)
        if "circle_clean_tests.jac" in filename:
            self.assertEqual(
                len(
                    [
                        i
                        for i in unified_diff(
                            before.splitlines(), after.splitlines(), n=0
                        )
                        if "test" not in i
                    ]
                ),
                5,
            )
        else:
            self.assertEqual(
                len("\n".join(unified_diff(before.splitlines(), after.splitlines()))),
                0,
            )


JacUnparseTests.self_attach_micro_tests()
