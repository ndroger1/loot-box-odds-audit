# Notebooks

Numbered and run in order, top to bottom (`01_...`, `02_...`). Together they reproduce every step from raw data to figures.

Failed approaches stay in. Each one gets a markdown cell explaining what went wrong and how it changed the direction of the analysis.

## Running in Google Colab

`00_colab_setup.ipynb` runs the same pipeline steps on a Colab machine and saves everything to your Google Drive. To open it: in Colab, choose **File → Open notebook → GitHub**, tick "Include private repos", and pick `notebooks/00_colab_setup.ipynb`. Or upload the file to Colab directly. The notebook explains the secrets it needs (`GITHUB_TOKEN`, `SCRAPER_CONTACT`) and the limits of collecting from a Colab machine (location, session time). Notebooks `01`–`05` stay the documented record and are run afterwards on the collected data.
