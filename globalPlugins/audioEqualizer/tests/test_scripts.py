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
        
        self.assertGreaterEqual(len(scripts), 29, 'Should have at least 29 scripts')
        for name, kw in scripts.items():
            self.assertIn('category', kw, f'{name} missing category')
            self.assertIn('description', kw, f'{name} missing description')
            self.assertNotIn('gesture', kw, f'{name} must not have a default gesture assigned')

    def test_secure_mode_cancels_load(self):
        init_path = os.path.join(os.path.dirname(__file__), '..', '__init__.py')
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('secureMode', content)
        self.assertIn('ActionCancelled', content)

if __name__ == '__main__':
    unittest.main()
