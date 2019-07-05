REM poetry run sphinx-apidoc -F -e -P .\hypercube -o docsource
poetry run sphinx-build .\docsource\ .\docs -d ./docsource/.cache