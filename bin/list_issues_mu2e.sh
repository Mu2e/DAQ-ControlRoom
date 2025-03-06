#
# This script clones all the repositories that are part of the 
# mu2e organization to the local directory structure

gh repo list mu2e --limit 4000 | while read -r repo _; do 
  gh issue list --repo "$repo"
done     
