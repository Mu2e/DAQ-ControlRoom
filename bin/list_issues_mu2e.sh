#
# This script list all the repositories that are part of the 
# mu2e organization to the local directory structure

#
# Set a token for the CLI to use
GH_TOKEN=`cat ~/.credentials/github.token`

# Get a list of repositories and then list
# the issues for each of them
gh repo list mu2e --limit 4000 | while read -r repo _; do 
  gh issue list --repo "$repo"
done     
