#\!/bin/bash

# Full logging
exec >> /var/log/git_autocommit.log 2>&1

# Ensure cron-safe environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=en_US.UTF-8
export PYTHONPATH=/usr/local/lib/python3.12/site-packages

echo "$(date '+%F %T') - Running git_autocommit"

# Single repository approach - track everything from /usr/local/bin
dir="/usr/local/bin"
cd "$dir" || exit 1

# Add all subdirectories and files to git tracking
echo "$(date '+%F %T') - Checking for changes in $dir and all subdirectories"

if [[ -n $(git status --porcelain) ]]; then
    echo "$(date '+%F %T') - Changes found in $dir"
    
    # Add all files including subdirectories
    git add -A .
    
    # Show what's being committed
    echo "$(date '+%F %T') - Files to be committed:"
    git status --short
    
    git commit -m "Auto-commit on $(date '+%F %T')"
    
    # Push to remote repository
    git push origin master
else
    echo "$(date '+%F %T') - No changes in $dir"
fi
EOF < /dev/null
