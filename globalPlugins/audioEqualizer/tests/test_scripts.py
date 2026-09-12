# -*- coding: utf-8 -*-
import unittest
import ast
import os

class TestScriptsConfiguration(unittest.TestCase):
    def test_all_scripts_have_category_and_description(self):
        init_path = os.path.join(os.path.dirname(__file__), '..', '__init__.py')
        with open(init_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        scripts = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('script_'):
                kwargs = {}
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        for kw in dec.keywords:
                            kwargs[kw.arg] = kw.value
                scripts[node.name] = kwargs
        
        self.assertGreaterEqual(len(scripts), 30, 'Should have at least 30 scripts')
        for name, kw in scripts.items():
            self.assertIn('category', kw, f'{name} missing category')
            self.assertIn('description', kw, f'{name} missing description')

if __name__ == '__main__':
    unittest.main()
