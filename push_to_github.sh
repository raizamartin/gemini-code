#!/bin/bash
set -e

# Colors for output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BLUE}Initializing Git repository and pushing to GitHub...${RESET}"

# Initialize Git repository
git init

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit of Gemini Code"

# Rename master branch to main
git branch -M main

# Add remote
git remote add origin https://github.com/raizamartin/gemini-code.git

# Push to GitHub
echo -e "${YELLOW}Pushing to GitHub...${RESET}"
echo -e "${YELLOW}You may be prompted for your GitHub credentials${RESET}"
git push -u origin main

echo -e "${GREEN}Successfully pushed to GitHub!${RESET}"
echo -e "${BLUE}Next steps:${RESET}"
echo -e "1. ${YELLOW}Build and publish to PyPI:${RESET}"
echo -e "   pip install --upgrade build twine"
echo -e "   python -m build"
echo -e "   python -m twine upload dist/*"
echo -e "2. ${YELLOW}Create a release on GitHub:${RESET}"
echo -e "   Visit: https://github.com/raizamartin/gemini-code/releases/new"