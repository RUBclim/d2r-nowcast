This file summarizes how to build the documentation both as HTML and PDF

# Documentation
The documentation for this repository is available in two formats: in HTML (intended) and PDF file (alternative).

Both can be built using Docker with the instructions below.

The PDF is also available pre-built under "./docs/d2r-nowcast.pdf" but may be out of date (see build date in PDF).

## Building the HTML
To build the HTML, first create a Docker-Image for the Sphinx-builder:

    docker build -f docs/sphinxdoc.Dockerfile -t sphinx_builder:v1 .

Then, navigate to the repositories' root directory and run the following command:

    docker run --rm -v $(pwd)/docs:/docs -u $(id -u ${USER}):$(id -g ${USER}) sphinx_builder:v1

The HTML can now be accessed via the "index.html" located in "./docs/build/html/index.html".

A known issue for building a new HTML if it has been built locally before is that certain parts may not be updated properly by rebuilding. To avoid this issue, it is advised to delete the "./docs/build/html" directory and build the html from scratch:

## Building the PDF

To build the PDF, first create a Docker-Image for the Sphinx-builder by running the following command feom the root dir (This will take some time):

    docker build -f docs/pdfbuilder.Dockerfile -t sphinx_pdf_builder:v1 .

Then, navigate to the repositories' root directory and run the following command:

    docker run --rm -v $(pwd)/docs:/docs -u $(id -u ${USER}):$(id -g ${USER}) sphinx_pdf_builder:v1

After running the builder, the PDF will be located under "./docs/build/pdf/d2rnowcast.pdf"

## Building Notes
The -u flag in `docker run` is used to avoid `root` owned directories getting created throughout the building process.

Also keep in mind to create the mounted volumes before executing `docker run`, to avoid them being `root` owned: `/docs/build/html` and `/docs/build/pdf`


## Updating Github Pages (manual mode)

1. Build HTML files as described above.
2. Copy content: ``cp -a docs/build/html/* docs``
3. Make sure that the ``repo > settings > pages > branch`` is set to ``/docs`` instead of ``/(root)``