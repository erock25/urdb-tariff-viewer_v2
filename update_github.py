#!/usr/bin/env python3
"""
GitHub Update Helper Script
Helps you update your project on GitHub and redeploy on Streamlit Cloud

Usage:
    python update_github.py "Your commit message here"
"""

import subprocess
import sys
import os

def run_git_command(command, description):
    """Run a git command and handle errors"""
    try:
        print(f"🔄 {description}...")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            if result.stdout.strip():
                print(result.stdout.strip())
        else:
            print(f"❌ Error during {description}:")
            if result.stderr:
                print(result.stderr.strip())
            return False

        return True

    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def update_github(commit_message):
    """Update the project on GitHub"""
    print("🚀 Updating project on GitHub...")
    print("=" * 50)

    # Check for changes
    if not run_git_command("git status --porcelain", "Checking for changes"):
        return False

    # Check if there are any changes to commit
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True, cwd=os.getcwd())
    if not result.stdout.strip():
        print("ℹ️  No changes detected. Nothing to update.")
        return True

    # Stage all changes
    if not run_git_command("git add .", "Staging changes"):
        return False

    # Commit changes
    if not run_git_command(f'git commit -m "{commit_message}"', f"Committing changes with message: '{commit_message}'"):
        return False

    # Push to GitHub
    if not run_git_command("git push", "Pushing to GitHub"):
        return False

    print("\n🎉 Project updated successfully on GitHub!")
    print("📱 Streamlit Cloud will automatically redeploy your app.")
    print("\n🔗 Your app URL: https://urdb-tariff-viewer-erock25.streamlit.app")

    return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a commit message!")
        print("\n📖 Usage:")
        print('   python update_github.py "Your commit message here"')
        print("\n📝 Examples:")
        print('   python update_github.py "Fix bug in cost calculator"')
        print('   python update_github.py "Add new tariff visualization"')
        print('   python update_github.py "Update dependencies"')
        sys.exit(1)

    commit_message = sys.argv[1]

    # Confirm the commit message
    print(f"📝 Commit message: '{commit_message}'")
    confirm = input("Continue? (y/n): ").lower().strip()

    if confirm not in ['y', 'yes']:
        print("❌ Update cancelled.")
        sys.exit(0)

    # Run the update
    success = update_github(commit_message)

    if success:
        print("\n✅ Update completed! Check your app in a few minutes.")
    else:
        print("\n❌ Update failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
