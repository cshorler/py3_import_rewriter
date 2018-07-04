#
# Copyright (c) 2018 - Chris HORLER
# License: Python Software Foundation V2 [https://opensource.org/licenses/Python-2.0]
#

import ast
import unittest
from itertools import zip_longest

import imp_rewriter

class ImportRewriterTests(unittest.TestCase):
    def ast_eq(self, node1, node2, msg=None):
        """https://stackoverflow.com/a/19598419 (improved)"""
        if type(node1) is not type(node2):
            raise self.failureException(f'{node1} != {node2}, {msg}')
        if isinstance(node1, ast.AST):
            for k, v in vars(node1).items():
                if k in ('lineno', 'col_offset', 'ctx'):
                    continue
                if not self.ast_eq(v, getattr(node2, k), msg):
                    raise self.failureException(f'{node1} != {node2}, {msg}')
            return True
        elif isinstance(node1, list):
            return all(self.ast_eq(n1, n2, msg) for n1, n2 in zip_longest(node1, node2))
        elif node1 != node2:
            raise self.failureException(f'{node1} != {node2}, {msg}')
        else:
            return True

    def setUp(self):
        self.addTypeEqualityFunc(ast.Module, self.ast_eq)
        
    def test_basic_import(self):
        mod_ref = ast.parse('import dummy', '<STRING>', 'exec')    
        mod_exp = ast.parse('import readline', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy', to_mod='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')
        
    def test_multi_import(self):
        mod_ref = ast.parse('import dummy1, dummy2, dummy3', '<STRING>', 'exec')
        mod_exp = ast.parse('import readline\nimport dummy1, dummy3', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy2', to_mod='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')

    def test_alias_basic_import(self):
        mod_ref = ast.parse('import dummy as magic_module', '<STRING>', 'exec')
        mod_exp = ast.parse('import readline as magic_module', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy', to_mod='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')

    def test_alias_multi_import(self):
        mod_ref = ast.parse('import dummy1 as d1, dummy2 as d2, dummy3 as d3', '<STRING>', 'exec')
        mod_exp = ast.parse('import readline as d2\nimport dummy1 as d1, dummy3 as d3', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy2', to_mod='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')

    def test_basic_importfrom(self):
        mod_ref = ast.parse('from dummy import magic', '<STRING>', 'exec')
        mod_exp = ast.parse('from rl import readline', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy', from_id='magic',
                                   to_mod='rl', to_id='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')

    def test_multi_importfrom(self):
        mod_ref = ast.parse('from dummy import magic1, magic2, magic3', '<STRING>', 'exec')
        mod_exp = ast.parse('from rl import readline\nfrom dummy import magic1, magic3', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy', from_id='magic2', to_mod='rl', to_id='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')

    def test_alias_basic_importfrom(self):
        mod_ref = ast.parse('from dummy import magic1 as m1', '<STRING>', 'exec')
        mod_exp = ast.parse('from readline import magic1 as m1', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy', to_mod='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')
       
    def test_alias_multi_importfrom(self):
        mod_ref = ast.parse('from dummy import magic1 as m1, magic2 as m2, magic3 as m3', '<STRING>', 'exec')
        mod_exp = ast.parse('from rl import readline as m2\nfrom dummy import magic1 as m1, magic3 as m3',
                            '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='dummy', from_id='magic2', to_mod='rl', to_id='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')
        
    def test_transform_import_to_importfrom(self):
        mod_ref = ast.parse('import readline', '<STRING>', 'exec')
        mod_exp = ast.parse('from rl import readline', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='readline', to_mod='rl', to_id='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')
        
    def test_transform_importfrom_to_import(self):
        mod_ref = ast.parse('from rl import readline', '<STRING>', 'exec')
        mod_exp = ast.parse('import readline', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='rl', from_id='readline', to_mod='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')
        
    def test_transform_multi_import_to_importfrom(self):
        mod_ref = ast.parse('import readline, sys, io', '<STRING>', 'exec')
        mod_exp = ast.parse('from rl import readline\nimport sys, io', '<STRING>', 'exec')
        imp_rewriter.RewriteImport(from_mod='readline', to_mod='rl', to_id='readline').visit(mod_ref)
        ast.fix_missing_locations(mod_ref)
        self.assertEqual(mod_ref, mod_exp, msg='AST transform failed')
        
        
if __name__ == '__main__':
    unittest.main()
    
