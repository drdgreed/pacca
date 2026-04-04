# api/__init__.py intentionally left empty.
#
# Do NOT import from .main here. main.py imports jose, fastapi, sqlalchemy,
# and other heavy dependencies at module level. Importing them eagerly here
# means every test that touches 'pacca.api.*' (even just routes or auth)
# would require the full server dependency stack to be installed.
#
# Tests import specific submodules directly:
#   from pacca.api.auth import validate_secret_key
#   from pacca.api.routes.admin import router
