#!/bin/bash

# Trading Dashboard - Setup Verification Script
# This script verifies that Epic A foundations are properly configured

set -e

echo "🔍 Trading Dashboard - Setup Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

check_directory() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

# Prerequisites
echo "1. Checking Prerequisites..."
echo "----------------------------"
check_command python3
check_command node
check_command npm
check_command psql
check_command git
echo ""

# Project Structure
echo "2. Checking Project Structure..."
echo "--------------------------------"
check_directory "apps/backend"
check_directory "apps/frontend"
check_directory "infra"
check_directory "tests"
check_directory "specs"
check_directory "docs"
echo ""

# Backend Files
echo "3. Checking Backend Files..."
echo "----------------------------"
check_file "apps/backend/requirements.txt"
check_file "apps/backend/app/main.py"
check_file "apps/backend/app/config.py"
check_file "apps/backend/.env.example"
check_file "apps/backend/Dockerfile"
check_file "apps/backend/alembic.ini"
echo ""

# Frontend Files
echo "4. Checking Frontend Files..."
echo "-----------------------------"
check_file "apps/frontend/package.json"
check_file "apps/frontend/tsconfig.json"
check_file "apps/frontend/vite.config.ts"
check_file "apps/frontend/tailwind.config.js"
check_file "apps/frontend/src/main.tsx"
check_file "apps/frontend/src/App.tsx"
echo ""

# Configuration Files
echo "5. Checking Configuration..."
echo "----------------------------"
check_file ".gitignore"
check_file ".editorconfig"
check_file "railway.toml"
check_file ".github/workflows/ci.yml"
check_file ".github/workflows/deploy.yml"
echo ""

# Documentation
echo "6. Checking Documentation..."
echo "----------------------------"
check_file "README.md"
check_file "SETUP.md"
check_file "docs/assumptions.md"
check_file "infra/railway-setup.md"
echo ""

# Test Files
echo "7. Checking Test Setup..."
echo "-------------------------"
check_file "apps/backend/pytest.ini"
check_file "apps/backend/tests/test_main.py"
check_file "apps/frontend/vitest.config.ts"
check_file "apps/frontend/src/App.test.tsx"
echo ""

# Summary
echo "=========================================="
echo -e "${YELLOW}Setup Verification Complete!${NC}"
echo ""
echo "Next Steps:"
echo "1. Install backend dependencies: cd apps/backend && pip install -r requirements.txt"
echo "2. Install frontend dependencies: cd apps/frontend && npm install"
echo "3. Configure .env files in both apps/backend and apps/frontend"
echo "4. Setup PostgreSQL database"
echo "5. Run tests to verify: pytest (backend) and npm test (frontend)"
echo ""
echo "See SETUP.md for detailed instructions."
