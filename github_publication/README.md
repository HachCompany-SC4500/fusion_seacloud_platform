# Publishing tools for GitHub
This folder contains some scripts to help the publication of source of open source components on GitHub environment.

Publication includes several steps:
* parse the manifest/layers/recipes to identify all related git repositories
* skip/redact Hach closed source repositories
* rework the git history to keep only a single commit and remove all history and comments
* update the recipes/manifests to use new created commits and github URL

By default, all recipes are scanned to find references to Stash repositories that will then be published.
Some sorting is done to ensure closed source repository are skipped.

If a new repository has to be pushed, it will be required to create it manually in the GitHub page (https://github.com/HachCompany-SC4500)

## Prepare environment for scripts executions
To prepare an environment ready to launch the script, we will use python virtualenv. A virtual environment where python binaries and libraries are installed to avoid global package installation.

First step is to ensure virtualenv is installed on the computer. If not, install it with:
  sudo apt-get install virtualenv

Then we create a virtual environment in a dedicated folder (e.g. : 'venv') with:
  virtualenv -p python3 venv

Warning: take care to venv location. If absolute path is long, you can have strange "bad interpreter" error.

To jump in the virtualenv, do:
  source venv/bin/activate

Then install required packages with:
  pip install -r requirements.txt

Then you can proceed with script prepare_repositories_for_publication.py
  <see bellow for details>

Exit the virtual environment with:
  deactivate

And finally, delete the environment if not needed anymore:
  rm -r venv

## Prepare repositories for publication
Call the prepare_repositories_for_publication.sh script to do the analysis and prepare sources for publication (see script help for parameters):
  ./prepare_repositories_for_publication.py Eagle/P2.84 "SC4500 R2023.4"

Modifications are done locally and nothing is pushed automatically.

Check for all repositories that the existing history has not been broken or that unexpected source code has not been included by error.

## Save to Stash
After verification, to save reworked source to Stash, use the following command:
  find repo/* -maxdepth 0 -type d -exec sh -c "cd {}; pwd ; git push origin github_publication_SC4500; echo " \\;

## Publish to GitHub
To publish reworked source to GitHub, use the following command:
  find repo/* -maxdepth 0 -type d -exec sh -c "cd {}; pwd ; git push github github_publication_SC4500; echo " \\;

## Final verification
Once everthing has been published to github, you can validate that every links are properly built by building a base image using standard OS command:
  repo init -u https://github.com/HachCompany-SC4500/fusion_seacloud_platform.git -b github_publication_SC4500
  repo sync
  source export
  bitbake eagle-x11-image

The build must succeed and a Eagle image without the proprietary stuffs (FCC,..) must be generated.


# Development features

## Clean working environment
During analysis all reposiories are cloned in the repo folder. If there is a need to rebuild the github branch from scratch, you can clean the cloned repositories using the clean.sh script:
  ./clean_repo.sh

## Updating python test requirements
During development you can require new python modules. In that case, install them with:
  pip install <module name>

When you have all your requirements installed, update the requirements.txt file accordingly. To do it launch:
  pip freeze > test/requirements.txt
