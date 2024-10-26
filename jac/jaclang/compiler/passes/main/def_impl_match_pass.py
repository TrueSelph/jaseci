"""Connect Decls and Defs in AST.

This pass creates links in the ast between Decls of Architypes and Abilities
that are separate from their implementations (Defs). This pass creates a link
in the ast between the Decls and Defs of Architypes and Abilities through the
body field.
"""

import jaclang.compiler.absyntree as ast
from jaclang.compiler.constant import Tokens as Tok
from jaclang.compiler.passes import Pass
from jaclang.compiler.passes.main import SubNodeTabPass
from jaclang.compiler.symtable import Symbol, SymbolTable


class DeclImplMatchPass(Pass):
    """Decls and Def matching pass."""

    def enter_module(self, node: ast.Module) -> None:
        """Enter module."""
        if not node.sym_tab:
            self.error(
                f"Expected symbol table on node {node.__class__.__name__}. Perhaps an earlier pass failed."
            )
        else:
            self.connect_def_impl(node.sym_tab)

    def after_pass(self) -> None:
        """Rebuild sub node table."""
        self.ir = SubNodeTabPass(input_ir=self.ir, prior=self).ir

    def defn_lookup(self, lookup: Symbol) -> ast.NameAtom | None:
        """Lookup a definition in a symbol table."""
        for defn in range(len(lookup.defn)):
            candidate = lookup.defn[len(lookup.defn) - (defn + 1)]
            if (
                isinstance(candidate.name_of, ast.AstImplNeedingNode)
                and candidate.name_of.needs_impl
            ):
                return candidate
        return None

    def connect_def_impl(self, sym_tab: SymbolTable) -> None:
        """Connect Decls and Defs."""
        for sym in sym_tab.tab.values():
            if isinstance(sym.decl.name_of, ast.AstImplOnlyNode):
                # currently strips the type info from impls
                arch_refs = [x[3:] for x in sym.sym_name.split(".")]
                name_of_links: list[ast.NameAtom] = []  # to link archref names to decls
                lookup = sym_tab.lookup(arch_refs[0])
                # If below may need to be a while instead of if to skip over local
                # import name collisions (see test: test_impl_decl_resolution_fix)
                if lookup and not isinstance(
                    lookup.decl.name_of, ast.AstImplNeedingNode
                ):
                    lookup = (
                        sym_tab.parent.lookup(arch_refs[0]) if sym_tab.parent else None
                    )
                decl_node = (
                    self.defn_lookup(lookup)
                    if len(arch_refs) == 1 and lookup
                    else lookup.defn[-1] if lookup else None
                )
                name_of_links.append(decl_node) if decl_node else None
                for name in arch_refs[1:]:
                    if decl_node:
                        lookup = (
                            decl_node.name_of.sym_tab.lookup(name, deep=False)
                            if decl_node.name_of.sym_tab
                            else None
                        )
                        decl_node = (
                            self.defn_lookup(lookup)
                            if len(arch_refs) == 1 and lookup
                            else lookup.defn[-1] if lookup else None
                        )
                        name_of_links.append(decl_node) if decl_node else None
                    else:
                        break
                if not decl_node:
                    continue
                elif isinstance(decl_node, ast.Ability) and decl_node.is_abstract:
                    self.warning(
                        f"Abstract ability {decl_node.py_resolve_name()} should not have a definition.",
                        decl_node,
                    )
                    continue
                if not isinstance(
                    valid_decl := decl_node.name_of, ast.AstImplNeedingNode
                ) or not (valid_decl.sym_tab and sym.decl.name_of.sym_tab):
                    raise self.ice(
                        f"Expected AstImplNeedingNode, got {valid_decl.__class__.__name__}. Not possible."
                    )
                valid_decl.body = sym.decl.name_of
                sym.decl.name_of.decl_link = valid_decl
                for idx, a in enumerate(sym.decl.name_of.target.archs):
                    a.name_spec.name_of = name_of_links[idx].name_of
                    a.name_spec.sym = name_of_links[idx].sym
                sym.decl.name_of.sym_tab.tab.update(valid_decl.sym_tab.tab)
                valid_decl.sym_tab.tab = sym.decl.name_of.sym_tab.tab
        for i in sym_tab.kid:
            self.connect_def_impl(i)

    def set_hasvar_initialized(
        self, method: ast.Ability, initialized: dict[str, bool]
    ) -> None:
        """Set True if a has var is initialized in the given method."""
        body: ast.SubNodeList[ast.CodeBlockStmt] | None = None
        if isinstance(method.body, ast.SubNodeList):
            body = method.body
        elif isinstance(method.body, ast.AbilityDef):
            body = method.body.body

        # TODO: maybe raise an internal compiler error as after decl and impl are connected
        # body should always exists.
        if body is None:
            return

        for stmnt in body.items:
            if not isinstance(stmnt, ast.Assignment):
                continue
            targets: ast.SubNodeList[ast.Expr] = stmnt.target
            for atom in targets.items:
                if not isinstance(atom, ast.AtomTrailer):
                    continue
                if (
                    not isinstance(atom.target, ast.SpecialVarRef)
                    or atom.target.name != "KW_SELF"
                ):
                    continue
                if not isinstance(atom.right, ast.Name):
                    continue

                # TODO: Here we can also check if an attribute is added dynamically to the instance which
                # is not present in the has var list however it should be in somewhere general to check
                # everywhere regarless of the init method.
                initialized[atom.right.value] = True

    def exit_architype(self, node: ast.Architype) -> None:
        """Exit Architype."""
        if node.arch_type.name == Tok.KW_OBJECT and isinstance(
            node.body, ast.SubNodeList
        ):
            # Key is the non-default attribute name,
            # value will set to true if it's initialized in the init body.
            non_default_attributes: dict[str, bool] = {}
            init_method: ast.Ability | None = None

            post_init_vars: list[ast.HasVar] = []
            postinit_method: ast.Ability | None = None

            for item in node.body.items:

                if isinstance(item, ast.ArchHas):
                    for var in item.vars.items:
                        if var.defer:
                            post_init_vars.append(var)
                        if var.value is None:
                            non_default_attributes[var.name.value] = False

                elif isinstance(item, ast.Ability):
                    if item.is_abstract:
                        continue
                    # Not sure if this is the correct way to check for init method.
                    if isinstance(item.name_ref, ast.SpecialVarRef):
                        if item.name_ref.name == "KW_INIT":
                            init_method = item
                        elif item.name_ref.name == "KW_POST_INIT":
                            postinit_method = item

            post_init_vars_names = [var.name.value for var in post_init_vars]

            if init_method is not None:
                self.set_hasvar_initialized(init_method, non_default_attributes)

                non_initialized_var_names = ", ".join(
                    [
                        f'"{name}"'
                        for name, is_init in non_default_attributes.items()
                        if (not is_init) and (name not in post_init_vars_names)
                    ]
                )
                if len(non_initialized_var_names) > 0:
                    self.error(
                        f"Non default attribute(s) {non_initialized_var_names} are not "
                        + "initialized in the init method.",
                        node_override=init_method.name_spec,
                    )

            # Check if postinit needed and not provided.
            if len(post_init_vars) != 0 and (postinit_method is None):
                self.error(
                    'Missing "postinit" method required by un initialized attribute(s).',
                    node_override=post_init_vars[0].name_spec,
                )  # We show the error on the first uninitialized var.

            # If postinit method is needed, ensure all the uninitialized vars are initialized in the postinit method.
            if len(post_init_vars_names) != 0 and (postinit_method is not None):
                self.set_hasvar_initialized(postinit_method, non_default_attributes)
                non_initialized_var_names = ", ".join(
                    [
                        f'"{name}"'
                        for name, is_init in non_default_attributes.items()
                        if not is_init and (name in post_init_vars_names)
                    ]
                )
                if len(non_initialized_var_names) > 0:
                    self.error(
                        f"Non default attribute(s) {non_initialized_var_names} are not "
                        + "initialized in the postinit method.",
                        node_override=postinit_method.name_spec,
                    )
