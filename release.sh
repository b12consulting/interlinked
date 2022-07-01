# Create distribution and publish it to Pypi
pip wheel .
twine upload interlinked-X.Y-py3-none-any.whl
