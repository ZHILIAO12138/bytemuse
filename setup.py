from setuptools import setup, find_packages
from Cython.Build import cythonize
import os


# Get all Python files
def get_py_files():
    py_files = []
    ladysite_path = os.path.join(os.path.dirname(__file__), 'modules', 'ladysite')
    ptsite_path = os.path.join(os.path.dirname(__file__), 'modules', 'ptsite')
    mongo_path = os.path.join(os.path.dirname(__file__), 'modules', 'mongo')
    for root, dirs, files in os.walk(ladysite_path):
        for file in files:
            py_files.append(os.path.join(root, file))
    for root, dirs, files in os.walk(ptsite_path):
        for file in files:
            py_files.append(os.path.join(root, file))
    for root, dirs, files in os.walk(mongo_path):
        for file in files:
            py_files.append(os.path.join(root, file))
    return py_files


setup(
    name='app',
    packages=find_packages(),
    ext_modules=cythonize(get_py_files(), compiler_directives={'language_level': "3"}),
    zip_safe=False
)
