# Description: Dockerfile for building sphinx documentation
FROM sphinxdoc/sphinx-latexpdf

# Extend the sphinx image with the rtd theme
RUN python3 -m pip install sphinx-rtd-theme sphinx-new-tab-link

# Build the Sphinx documentation when the container runs
CMD ["sphinx-build", "-M", "latexpdf", "source", "build"]


## BUILD ##

# Build an image with this command. Make sure you cd to the root of the project before running this command
# 	docker build -f doc/pdfbuilder.Dockerfile -t sphinx_pdf_builder:v1 .


## RUN ##

# To re-build the pdf, it is advisable to remove the entire build directory.
# Make sure you cd to the root of the project before running this command and confirm the path before running this command!
#    rm -rf doc/build

# Run image for PDF output. Make sure you cd to the root of the project before running this command
#	docker run --rm -v $(pwd)/doc:/docs  -u $(id -u ${USER}):$(id -g ${USER}) sphinx_pdf_builder:v1

# add -u flag if non-root execution is wanted
