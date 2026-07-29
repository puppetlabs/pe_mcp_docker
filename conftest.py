"""Root conftest — pytest inserts this file's directory into sys.path,
which is what makes `import proxy` / `import cli` / `import selftest`
resolve from tests/, since these are flat py-modules, not a package.
"""
