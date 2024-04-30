#!/usr/bin/env python3

import logging
import sys
import os
import argparse

import xml.etree.ElementTree as ET
from git import Repo
from git import IndexFile
import subprocess
import shlex
import shutil

# WARNING: only use if you want the overwrite an existing branch
# To ignore the existing remote github_publication branch and restart from scratch
# Use it after a clean to remove all local branches
dont_use_existing_remote_github_branch=False

# Controller name targetted (will be used to build branch names and github URL)
controller_name='SC4500'

# Branch use to store github publication (in stash and github)
github_branch_name='github_publication_' + controller_name

# Remote name for github
github_remote_name='github'
# For github access via SSH (Github remote for Hach)
github_remote_url='git@github.com:HachCompany-' + controller_name

# For github download in manifest
github_http_url='https://github.com/HachCompany-' + controller_name
# For github download in recipe
github_git_url='git://github.com/HachCompany-' + controller_name

# marker that needs to be replaced within the command_find_file
marker_to_replace = "[to_replace]"
# command to find one specific file, uses a marker to be replaced
command_find_file = "find repo -type f -iname \"" + marker_to_replace + "\""
# command to find one specific recipe, uses a marker to be replaced
command_find_recipe = "find repo -type d -iname \"" + marker_to_replace + "\""
# command to empty the content of file
command_empty_file = "truncate -s 0 \"" + marker_to_replace + "\""
# command to redact emails
command_redact_emails = "find repo -type f -not -path '*/.git/*' -exec sed -i -e 's///g' -e 's///g' {} + "

def parse_command_line():
    """ Returns parsed command line arguments """
    parser = argparse.ArgumentParser(description='Rework Eagle Yocto sources to prepare publication to github.', epilog='e.g.: ./prepare_repositories_for_publication.py release/EagleP2.84 "SC4500 R2023.4"')
    parser.add_argument('tag', metavar='<tag>', help='the tag of platform repository that points the revision to append to publication branch')
    parser.add_argument('message', metavar='<message>', help='message that will be used as commit message for all reworked repositories')
    logging.debug('Parse command line parameters: {0}'.format(parser.parse_args()))
    return parser.parse_args()


def get_commit_from_tag(manifest_repository_properties):
    """ Returns commit that matches the tag if any, None otherwise """
    logging.debug('Verify that the tag "{0}" is present in repository {1}'.format(manifest_repository_properties['revision'], manifest_repository_properties['name']))
    repo = checkout_repository(manifest_repository_properties)
    repo.remotes.origin.fetch()
    if tag not in repo.tags:
        logging.error('ERROR: The tag "{0}" is not found in repository {1}'.format(tag,repository_location))
        return None

    tag_commit = repo.tags[tag].commit
    logging.debug('The commit for tag "{0}" is {1}'.format(tag, tag_commit))
    return tag_commit

def rework_manifest_for_github(manifest_repository_properties, message):
    """ Rework the manifest repository to be ready to be published on github """
    print('Rework for github manifest {0} revision {1}'.format(manifest_repository_properties['name'], manifest_repository_properties['revision']))

    manifest_repo = checkout_repository(manifest_repository_properties)
    layers_references = get_references_from_manifest(manifest_repo)
    for repository_properties in layers_references:
        new_repository_properties = rework_layer_for_github(repository_properties, message)
        update_layer_reference_in_manifest(repository_properties, new_repository_properties)
        print("")

    if manifest_repo.is_dirty():
        commit_pending_changes(manifest_repo, 'Intermediate manifest commit to include updated layers - will be removed during history rework')
    new_manifest_properties = rework_repository_history(manifest_repo, message)

def checkout_repository(repository_properties):
    """ Checkout repository and return the repo object """
    # Clone repo in a temporary location from Yocto downloaded repo
    repo_location=os.path.join("repo",repository_properties['name'])
    if not os.path.exists(repo_location):
        logging.debug("Clone repository: {0} ({1}) into {2}".format(repository_properties['name'], repository_properties['revision'], repo_location))
        os.makedirs(repo_location)
        repo = Repo.clone_from(repository_properties['url'].replace('git://','ssh://') + '/' + repository_properties['name'], repo_location)
    else:
        logging.debug("Checkout repository: {0} ({1}) into {2}".format(repository_properties['name'], repository_properties['revision'], repo_location))
        repo = Repo(repo_location)
        repo.remotes.origin.fetch()

    repo.head.reset(index=True, working_tree=True)
    repo.head.reference = repo.commit(repository_properties["revision"])
    repo.head.reset(index=True, working_tree=True)
    return repo

def get_references_from_manifest(manifest_repo):
    """ Returns hach layers references as a list of repository layers properties (name, url, revision, path, source,...) """
    print("Search Hach layers in current manifest")
    repository_location=manifest_repo.working_tree_dir
    manifest_filename = os.path.join(repository_location, 'default.xml')
    tree = ET.parse(manifest_filename)
    root = tree.getroot()
    # Get original HACH remote URL
    # Typically : ssh://git@stash.waterqualitytools.com:7999/fcfw
    hach_remote = root.find("./remote[@name='hach']")
    hach_url = hach_remote.attrib["fetch"]

    # Get properties for each Hach layers
    layers=[]
    for child in root.findall("./project[@remote='hach']"):
        layers.append({
                "name": child.attrib["name"],
                "path": child.attrib["path"],
                "revision": child.attrib["revision"],
                "url": hach_url,
                "source": {
                    'type': 'manifest',
                    'files': [manifest_filename]
                    }
                })
    print("  Hach layers found:")
    for layer in layers:
        print("    {0}/{1} ({2})".format(layer["url"], layer["name"], layer["revision"]))
    print("")
    return layers

def rework_layer_for_github(layer_repository_properties, message):
    """ Rework a layer repository to be ready to be published on github and returns its new properties """
    print("Rework for github layer: {0}".format(layer_repository_properties['name']))
    layer_repo = checkout_repository(layer_repository_properties)
    repository_references = get_references_from_layer(layer_repo)
    for repository_properties in repository_references:
        updated_repository_properties = rework_repository_for_github(repository_properties, message)
        update_reference_in_layer(repository_properties, updated_repository_properties)

    # Filter FCCtest.tar.gz file that contains an old FCC source code
    if 'meta-seacloud' in layer_repository_properties['name']:
        print("Delete any FCCtest.tar.gz file found in the layer tree")
        os.system("find {0} -type f -name FCCtest.tar.gz -exec rm {{}} \;".format(layer_repo.working_tree_dir))	

    # Ensure to redact any sensible/proprietary data from repos
    remove_sensible_data()

    if layer_repo.is_dirty():
        commit_pending_changes(layer_repo, 'Intermediate layer commit to include updated repositories - will be removed during history rework')
    layer_properties = rework_repository_history(layer_repo, message)
    return layer_properties

def update_layer_reference_in_manifest(repository_properties, new_repository_properties):
    """ Update references to layer in a manifest """
    print("Update manifest for {0}".format(repository_properties['name']))
    for file in repository_properties['source']['files']:
        logging.debug("In file {0}".format(file))
        tree = ET.parse(file)
        root = tree.getroot()

        # Update Hach stash URL by GitHub one
        hach_remote = root.find("./remote[@name='hach']")
        hach_remote.attrib["fetch"] = github_http_url # new_repository_properties['url']

        # Update layer properties
        for child in root.findall("./project[@name='" + repository_properties['name'] + "']"):
            print("Replace reference to {0} ({1}) by ({2})".format(repository_properties['name'], repository_properties['revision'],new_repository_properties['revision']))
            child.attrib["revision"] = new_repository_properties['revision']
        tree.write(file)

def get_references_from_layer(layer_repo):
    """ Search references to other repositories and returns a list of repository references (revision, branch, url, name, files) """
    # Add within this array the files that lead to non expected repository
    files_to_skip = ['seacloudapp', 'README.md', 'persistent-storage.inc', 'befe.inc']

    repository_location=layer_repo.working_tree_dir
    logging.debug("Search linked repositories in {0}".format(repository_location))

    repo_references = {}
    logging.debug("Look for usage of hach stash repositories (git@stash.waterqualitytools.com)")
    result = subprocess.run( shlex.split("egrep -R -l '(git@stash.waterqualitytools.com|git@stash.hach.ewqg.com)' --exclude-dir='.git' " + repository_location), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL )
    recipe_files=result.stdout.decode('utf-8').splitlines()
    if recipe_files:
        logging.debug("Identified recipe using hach stash repositories (stash.waterqualitytools.com):")
        for file in recipe_files:
            print("  {0}".format(file))

    for file in recipe_files:
        if any(key in file for key in files_to_skip):
            print("Ignoring file {0}".format(file))
            continue
        logging.debug("Parsing {0} for references".format(file))
        reference = extract_reference_from_recipe(file)
        reference['source'] = { 'type': 'recipe' }
        logging.debug("References found: {0}".format(reference))
        key = reference['url'] + '_' + reference['name'] + '_' + reference['branch'] + '_' + reference['revision']
        # Retrieve existing reference or use the current one if none
        reference = repo_references.get(key, reference)
        # Retrieve existing files list or create a new one if none
        files = reference['source'].get('files',[])
        # Add the current file to the list
        files.append(file)
        # Update the files property
        reference['source']['files'] = files
        # Create or update the reference for current key
        repo_references[key] = reference

    if not repo_references:
        print("No repository reference found")
    else:
        print("Reference found:")
        for key, properties in repo_references.items():
            print("  {0}/{1} {2} ({3}) ".format(properties['url'], properties['name'], properties['branch'], properties['revision']))
            logging.debug("Key: {0}".format(key))
            logging.debug("Properties: {0}".format(properties))
    return repo_references.values()

def update_reference_in_layer(repository_properties, updated_repository_properties):
    """ Update references to repositories in a layer """
    print("Update layer from {0} ({1}) to {2} ({3})".format(repository_properties['branch'], repository_properties['revision'], updated_repository_properties['branch'], updated_repository_properties['revision'],))
    for file in repository_properties['source']['files']:
        logging.debug("In file {0}".format(file))

        old_url = repository_properties['url'] +'/' + repository_properties['name']
        new_url = updated_repository_properties['url'] +'/' + repository_properties['name']
        logging.debug("Replace {0} by {1}".format(old_url, new_url))
        os.system("sed -i 's#" + old_url + ".*;protocol=ssh#" + new_url + "#gI' " + file)

        logging.debug("Replace {0} by {1}".format(repository_properties['revision'], updated_repository_properties['revision']))
        os.system("sed -i 's/" + repository_properties['revision'] + "/" + updated_repository_properties['revision'] + "/gI' " + file)

        logging.debug("Replace {0} by {1}".format(repository_properties['branch'], updated_repository_properties['branch']))
        # Depending on recipes, the branch can be specified with SRCBRANCH or BRANCH variable
        os.system("sed -i 's/^SRCBRANCH.*" + repository_properties['branch'] + ".*$/SRCBRANCH=\"" + updated_repository_properties['branch'] + "\"/gI' " + file)
        os.system("sed -i 's/^BRANCH.*" + repository_properties['branch'] + ".*$/BRANCH = \"" + updated_repository_properties['branch'] + "\"/gI' " + file)

def extract_reference_from_recipe(file):
    """ Return properties of the reference found in file (url, branch, revision, name) """
    result = subprocess.run( shlex.split("egrep -o '(git://git@stash.waterqualitytools.com|git://git@stash.hach.ewqg.com)[^;]*;' " + '"' + file + '"'), stdout=subprocess.PIPE )
    matches=result.stdout.decode('utf-8').strip().splitlines()
    if len(matches)>1:
        print("ERROR: too many URL found for this reference to stash in {0} : {1}".format(file, matches))
        exit(1)
    # Typically git://git@stash.waterqualitytools.com:7999/fcfw/fusion_fw_common.git
    url = matches[0].replace(';','').strip()

    result = subprocess.run( shlex.split('grep ^SRCREV "' + file + '"'), stdout=subprocess.PIPE )
    matches=result.stdout.decode('utf-8').strip().splitlines()
    if len(matches)>1:
        print("ERROR: too many SHA1 found for this reference to stash in {0} : {1}".format(file, matches))
        exit(1)
    sha1 = matches[0].split("=")[1].replace('"','').strip()

    result = subprocess.run( shlex.split('grep ^SRCBRANCH "' + file + '"'), stdout=subprocess.PIPE )
    matches=result.stdout.decode('utf-8').strip().splitlines()
    if len(matches)>1:
        print("ERROR: too many branch found for this reference to stash in {0} : {1}".format(file, matches))
        exit(1)
    if not matches:
        result = subprocess.run( shlex.split('grep ^BRANCH "' + file + '"'), stdout=subprocess.PIPE )
        matches=result.stdout.decode('utf-8').strip().splitlines()
        if len(matches)>1:
            print("ERROR: too many branch found for this reference to stash in {0} : {1}".format(file, matches))
            exit(1)

    branch = matches[0].split("=")[1].replace('"','').strip()
    name = url.split("/")[-1]
    url = url.replace("/" + name, '')
    return { 'url':url, 'branch':branch, 'revision':sha1, 'name':name }

def rework_repository_for_github(repository_properties, message):
    """ Rework the repository history to be ready to be published on github """
    print("Rework repository for github: {0}".format(repository_properties['name']))
    repo = checkout_repository(repository_properties)
    new_repository_properties = rework_repository_history(repo, message)
    print("")
    return new_repository_properties

def rework_repository_history(repo, commit_message):
    """ Use current tree to create a new commit on <github_branch_name> branch and returns corresponding references (updated for github) """
    print("Rework repository history on {0}".format(repo.working_tree_dir))

    origin_url = repo.remotes.origin.url
    name = origin_url.split("/")[-1]

    # Add github remote later used to manually push stuff on GitHub
    github_ssh_url = "{0}/{1}".format(github_remote_url, name)
    logging.debug("Github remote url {0}".format(github_ssh_url))
    logging.debug("Github remote branch {0}".format(github_branch_name))
    if github_remote_name in repo.remotes:
        github = repo.remotes[github_remote_name]
    else:
        github = repo.create_remote(github_remote_name, github_ssh_url)

    # Get or create the local github branch to commit on
    if github_branch_name in repo.heads:
        logging.debug("Reuse local branch {0}".format(github_branch_name))
        github_branch=repo.heads[github_branch_name]
        commit_parent = [github_branch.commit]
    else:
        origin=repo.remotes.origin
        if github_branch_name not in origin.refs or dont_use_existing_remote_github_branch:
            logging.debug("Create a new branch {0}".format(github_branch_name))
            github_branch=repo.create_head(github_branch_name)
            commit_parent = []
        else:
            logging.debug("Create a new local branch {0} synchronized with remote".format(github_branch_name))
            github_branch=repo.create_head(github_branch_name, origin.refs[github_branch_name])
            commit_parent = [github_branch.commit]


    # Reset on current commit to remove possible pending modifications
    repo.head.reset(index=True, working_tree=True)

    # Reuse the tree referenced by the current commit to keep the data
    # but create a new commit with selected message and proper parent commit
    current_tree = repo.head.commit.tree
    logging.debug("Current tree reference is: {0}".format(current_tree.hexsha))
    logging.debug("Point on {0} branch".format(github_branch_name))
    repo.head.reference = github_branch
    logging.debug("Create an index using current tree")
    new_index = IndexFile.from_tree(repo, current_tree)
    logging.debug("Create a new commit using current index")
    new_index.commit(message = commit_message, parent_commits=commit_parent)
    logging.debug("Write commit to repository")
    new_index.write()
    print("Commit created: {0} ({1})".format(github_branch_name, repo.head.commit.hexsha))
    logging.debug("Commit written is: {0}".format(repo.head.commit.hexsha))

    return { 'name': name,'url':github_git_url, 'revision':repo.head.commit.hexsha, 'branch':github_branch_name}

def get_files_path(files_to_find):
    """ Find and return the complete path of provided files """
    matches = []
    for key in files_to_find:
        try:
            result = subprocess.run(shlex.split(command_find_file.replace(marker_to_replace, key)),
                stdout=subprocess.PIPE).stdout.decode('utf-8').strip().splitlines()
            matches += result
        except Exception as e:
            print("Error in get_files_path: ", e)
    return matches

def redact_files_data(files):
     """ Redact by emptying the provided files """
     for file in files:
        try:
            subprocess.run(shlex.split(command_empty_file.replace(marker_to_replace, file)),
                stdout=subprocess.PIPE)
        except Exception as e:
            print("Error in redact_files_data: ", e)   
            
def delete_recipe_folder(recipes):
    """ Delete the provded recipes folder """
    for recipe in recipes:
        try:
            recipe_path = subprocess.run(shlex.split(command_find_recipe.replace(marker_to_replace, recipe)),
                stdout=subprocess.PIPE).stdout.decode('utf-8').strip().splitlines()
            if len(recipe_path) == 1:
                shutil.rmtree(recipe_path[0])
        except Exception as e:
            print("Error in delete_recipe_folder: ", e)

def redact_emails():
    """ Refact emails from patch/header files """
    try:
        subprocess.run(shlex.split(command_redact_emails),stdout=subprocess.PIPE)
    except Exception as e:
        print("Error in redact_emails: ", e)

def remove_sensible_data():
    """ Remove recipes and redact files that are containing proprietary code or sensible information """
    # the different path to files that contains sensible information and will need to be removed
    files_to_redact = []

    # list of authentication keys that are currently within the repo and need redaction
    authentication_keys = ["*.pem", "*.pub", "authorized_keys", "password", "SeaCloudGlobalKey"]
    # list of specific files that are containing sensible data
    sensible_files = ["swupdate-unlock.sh", "generate_keys.sh", "grant_access.sh", "option-key-decoder.c", "CA", "create_service_logs.sh", "npm-shrinkwrap.json"]
    # list of specific recipe that needs to be deleted
    recipes_to_redact = ["ee-logger", "recipes-python-scripts", "recipes-fcc", "recipes-diagnose"]

    files_to_redact += get_files_path(authentication_keys)
    files_to_redact += get_files_path(sensible_files)

    redact_files_data(files_to_redact)
    delete_recipe_folder(recipes_to_redact)
    redact_emails()

def commit_pending_changes(repo, message):
    """ Commit current pending changes with message as commit message """
    logging.debug("Commit pending changes")
    files = repo.git.diff(name_only=True).strip().splitlines()
    logging.debug("Files are {0}".format(files))
    for file in files:
        logging.debug("Add {0}".format(file))
        repo.git.add(file)
    logging.debug("Commit files")
    repo.git.commit('-m', message)
    print("Commit ({0}) {1}".format(repo.head.commit.hexsha, message))

if __name__ == "__main__":
    args = parse_command_line()
    tag = args.tag
    message = args.message

    manifest_properties = {'name':'fusion_seacloud_platform.git','url':'ssh://git@stash.waterqualitytools.com:7999/fcfw', 'revision':tag}

    print("The tag {0} from platform repository {1} will be cloned for analysis".format(tag, manifest_properties['name']))
    print("The new commit generated will use the message: '{0}'".format(message))
    print('')

    tag_commit = get_commit_from_tag(manifest_properties)
    if tag_commit is None:
        print("Abort! Can't find the commit revision for the requested tag")
        sys.exit(1)

    manifest_properties['revision'] = tag_commit
    rework_manifest_for_github(manifest_properties, message)

    print('')
    print("Launch following command to push all repositories to github")
    print('   find repo/* -maxdepth 0 -type d -exec sh -c "cd {}; pwd ; git push github ' + github_branch_name + '; echo " \;')
    print('')
    print("Launch following command to update " + github_branch_name + " branch of all hach repositories")
    print('   find repo/* -maxdepth 0 -type d -exec sh -c "cd {}; pwd ; git push origin ' + github_branch_name + ';echo " \;')

