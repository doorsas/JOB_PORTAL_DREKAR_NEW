#!/bin/bash
# Git-based deployment helper for HR Portal
# Use this script to push changes and deploy to Ubuntu server

set -e

# Configuration
REMOTE_USER="ubuntu"  # Change to ubuntu user
REMOTE_HOST="3.124.14.179"
REMOTE_PATH="/var/www/hr-portal"
SSH_KEY="~/.ssh/drekar_work.pem"  # Your existing SSH key

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_warning "Not in a Git repository. Initializing..."
    git init
    git add .
    git commit -m "Initial commit for HR Portal"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_status "You have uncommitted changes. Committing them..."
    git add .
    echo "Enter commit message (or press Enter for default):"
    read -r commit_message
    if [ -z "$commit_message" ]; then
        commit_message="Update HR Portal - $(date '+%Y-%m-%d %H:%M')"
    fi
    git commit -m "$commit_message"
    print_success "Changes committed: $commit_message"
fi

# Push to remote repository (if configured)
if git remote | grep -q origin; then
    print_status "Syncing with remote repository..."

    # Try to pull first to sync
    if git pull origin master --no-edit; then
        print_success "Synced with remote repository"
    else
        print_warning "Pull failed. Checking status..."

        # Check if remote is ahead
        git fetch origin
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/master)

        if [ "$LOCAL" != "$REMOTE" ]; then
            print_warning "Local and remote branches have diverged."
            echo "Options:"
            echo "1) Force push (overwrites remote - use with caution)"
            echo "2) Manual merge (recommended)"
            echo "3) Cancel deployment"
            read -p "Choose option (1/2/3): " sync_choice

            case $sync_choice in
                1)
                    print_warning "Force pushing to remote..."
                    git push origin master --force
                    ;;
                2)
                    print_status "Please resolve conflicts manually:"
                    echo "1. Run: git pull origin master"
                    echo "2. Resolve any merge conflicts"
                    echo "3. Run: git add . && git commit -m 'Merge conflicts resolved'"
                    echo "4. Run this script again"
                    exit 1
                    ;;
                3)
                    print_status "Deployment cancelled"
                    exit 0
                    ;;
            esac
        fi
    fi

    # Now try to push
    print_status "Pushing to remote repository..."
    if git push origin master; then
        print_success "Successfully pushed to remote repository"
    else
        print_warning "Push failed. You may need to resolve conflicts manually."
        echo "Try running: git pull origin master"
        echo "Then resolve conflicts and run this script again."
        exit 1
    fi
else
    print_warning "No remote repository configured."
    echo "To set up a remote repository:"
    echo "git remote add origin <your-repository-url>"
    echo "git push -u origin master"
    echo "Continue with local deployment? (y/n)"
    read -r continue_local
    if [ "$continue_local" != "y" ]; then
        exit 0
    fi
fi

# Deploy to server
print_status "Deploying to Ubuntu server..."
echo "Choose deployment method:"
echo "1) SSH deployment (requires SSH key setup)"
echo "2) Manual instructions"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        # Check if your specific SSH key exists
        if [ -f ~/.ssh/drekar_work.pem ]; then
            print_status "Deploying via SSH using existing key..."

            # Copy update script to server
            scp -i ~/.ssh/drekar_work.pem update-deploy.sh $REMOTE_USER@$REMOTE_HOST:/tmp/

            # Execute deployment on server
            ssh -i ~/.ssh/drekar_work.pem $REMOTE_USER@$REMOTE_HOST "sudo bash /tmp/update-deploy.sh"

            print_success "Deployment completed!"
        else
            print_error "SSH key 'drekar_work.pem' not found at ~/.ssh/drekar_work.pem"
            echo "Please ensure your SSH key is in the correct location."
            echo "Current expected path: ~/.ssh/drekar_work.pem"
            echo
            echo "If your key is in a different location, please:"
            echo "1. Copy it to ~/.ssh/drekar_work.pem"
            echo "2. Or update the SSH_KEY variable in this script"
            echo "3. Or use manual deployment method (option 2)"
        fi
        ;;
    2)
        print_status "Manual deployment instructions:"
        echo
        echo "1. Copy your project files to the server:"
        echo "   scp -i ~/.ssh/drekar_work.pem -r . $REMOTE_USER@$REMOTE_HOST:/tmp/hr-portal-update/"
        echo
        echo "2. SSH into your server:"
        echo "   ssh -i ~/.ssh/drekar_work.pem $REMOTE_USER@$REMOTE_HOST"
        echo
        echo "3. Run the update script:"
        echo "   sudo bash /var/www/hr-portal/update-deploy.sh"
        echo
        echo "   OR manually copy files:"
        echo "   sudo cp -r /tmp/hr-portal-update/* /var/www/hr-portal/"
        echo "   sudo chown -R www-data:www-data /var/www/hr-portal"
        echo "   sudo systemctl restart hr-portal"
        echo "   sudo systemctl reload nginx"
        ;;
    *)
        print_warning "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

print_success "Git deployment process completed!"
echo
echo "🌐 Your HR Portal should now be updated at: https://$REMOTE_HOST"
echo "📊 Check the application and monitor logs for any issues."