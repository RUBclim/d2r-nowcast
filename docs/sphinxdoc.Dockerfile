# Description: Dockerfile for building sphinx documentation
FROM sphinxdoc/sphinx

# Extend the sphinx image with the rtd theme
RUN python3 -m pip install sphinx-rtd-theme sphinx-new-tab-link

# Build the Sphinx documentation when the container runs
CMD ["make", "html"]


## BUILD ##

# Build an image with this command. Make sure you cd to the root of the project before running this command
# 	docker build -f docs/sphinxdoc.Dockerfile -t sphinx_builder:v1 .


## RUN ##

# To re-build the html, it is advisable to remove the entire build directory.
# Make sure you cd to the root of the project before running this command and confirm the path before running this command!
#   rm -rf docs/_build

# Run image with this command. Make sure you cd to the root of the project before running this command
# 	docker run --rm -v $(pwd)/docs:/docs  -u $(id -u ${USER}):$(id -g ${USER}) sphinx_builder:v1


