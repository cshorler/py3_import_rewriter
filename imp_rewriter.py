#
# Copyright (c) 2018 - Chris HORLER
# License: Python Software Foundation V2 [https://opensource.org/licenses/Python-2.0]
#

import ast
import importlib.abc
import importlib.machinery

class RewriteImport(ast.NodeTransformer):
    def __init__(self, from_mod=None, from_id=None, to_mod=None, to_id=None):
        super().__init__()
        self._from_mod = from_mod
        self._from_id = from_id
        self._to_mod = to_mod
        self._to_id = to_id
        self._stmt_types = ['Module', 'If', 'Try']

    def _update_ImportFrom(self, node, stmt_list, idx):
        if node.module != self._from_mod:
            return
        elif self._from_id and not any(x for x in node.names if x.name == self._from_id):
            return

        # prepare alias changes
        if self._from_id:
            new_names = []
            for i, alias in enumerate(node.names[:]):
                if alias.name == self._from_id:
                    new_names.append(ast.alias(self._to_id, alias.asname))
                    del node.names[i]

            if not node.names:
                del stmt_list[idx]
        
        # select type of change based on instance parameters
        if self._from_mod and self._from_id and self._to_mod and self._to_id:
            new_node = ast.ImportFrom(module=self._to_mod, level=0, names=new_names)
            stmt_list.insert(idx, new_node)
        elif self._from_mod and self._from_id and self._to_mod:
            new_node = ast.Import(names=[ast.alias(self._to_mod, None),])
            stmt_list.insert(idx, new_node)
        elif self._from_mod and self._to_mod:
            new_node = ast.ImportFrom(module=self._to_mod, level=0, names=node.names)
            stmt_list[idx] = new_node
        else:
            raise ValueError("unexpected argument combination")
    
    def _update_Import(self, node, stmt_list, idx):
        if not any(x for x in node.names if x.name == self._from_mod):
            return
        
        new_names = []
        for i, alias in enumerate(node.names[:]):
            if alias.name == self._from_mod:
                new_names.append(alias)
                del node.names[i]

        if not node.names:
            del stmt_list[idx]
            
        if self._to_mod and self._to_id:
            for alias in new_names:
                new_node = ast.ImportFrom(module=self._to_mod, level=0, names=[alias,])
                stmt_list.insert(idx, ast.copy_location(new_node, node))
        elif self._to_mod:
            for alias in new_names:
                new_node = ast.Import(names=[ast.alias(self._to_mod, alias.asname),])
                stmt_list.insert(idx, ast.copy_location(new_node, node))
    
    def _update_StmtList(self, node):
        for idx, stmt in enumerate(node.body[:]):
            if isinstance(stmt, ast.Import) and not self._from_id:
                self._update_Import(stmt, node.body, idx)
            elif isinstance(stmt, ast.ImportFrom):
                self._update_ImportFrom(stmt, node.body, idx)
        self.generic_visit(node)
        return node
    
    def __getattr__(self, name):
        if name in ['visit_' + x for x in self._stmt_types]:
            return self._update_StmtList
        else:
            raise AttributeError
        
class CheckImports(ast.NodeVisitor):
    def __init__(self, name, from_mod=None, from_id=None):
        super().__init__()
        self._name = name
        self._from_mod = from_mod
        self._from_id = from_id
        self.has_import = False
                
    def visit_Import(self, node):
        if any(x.name == self._from_mod for x in node.names):
            self.has_import = True
            
    def visit_ImportFrom(self, node):
        if node.module == self._from_mod:
            self.has_import = True
        

class RewriteImportLoader(importlib.abc.Loader, importlib.machinery.PathFinder):
    def __init__(self, from_mod=None, from_id=None, to_mod=None, to_id=None):
        super().__init__()
        self._from_mod = from_mod
        self._from_id = from_id
        self._to_mod = to_mod
        self._to_id = to_id
        
    def find_spec(self, fullname, path=None, target=None):
        spec = super().find_spec(fullname, path, target)
        
        if spec:
            chk = CheckImports(fullname, self._from_mod, self._from_id)
            spec.loader = self
            if spec.origin.endswith('.py'):
                with open(spec.origin, 'r') as f:
                    mod_raw = f.read()
                    mod_ast = ast.parse(mod_raw, spec.origin, 'exec')
                    chk.visit(mod_ast)
            if chk.has_import or fullname == self._from_mod:
                return spec
        return None
        
    def exec_module(self, module):
        if module == self._from_mod:
            return
        with open(module.__spec__.origin, 'r') as f:
            mod_raw = f.read()
            mod_ast = ast.parse(mod_raw, module.__spec__.origin, 'exec')
            RewriteImport(from_mod=self._from_mod, from_id=self._from_id,
                          to_mod=self._to_mod, to_id=self._to_id).visit(mod_ast)
            ast.fix_missing_locations(mod_ast)
            module._ast_mod = mod_ast
        mod_code = compile(module._ast_mod, '<AST>', 'exec')
        exec(mod_code, module.__dict__)


