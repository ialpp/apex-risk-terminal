import sys
import importlib

# Test importing all views
import os

base = r'C:\Users\İsmail Alp\Desktop\PROJELER\Kredi_Skoru_tahminleyici\ui\views'
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            rel_path = os.path.relpath(os.path.join(root, f), base)
            module_name = 'ui.views.' + rel_path.replace(os.sep, '.')[:-3]
            try:
                importlib.import_module(module_name)
            except Exception as e:
                print(f'Failed to import {module_name}: {e}')

print('Import test finished.')
