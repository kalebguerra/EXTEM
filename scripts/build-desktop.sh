#!/bin/bash
# Build script for AI Image Generator Manager Desktop Application

set -e

echo "🚀 Building AI Image Generator Manager Desktop Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "Python is not installed. Please install Python first."
    exit 1
fi

# Set Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

print_status "Using Python: $PYTHON_CMD"

# Install root dependencies
print_status "Installing root dependencies..."
npm install

# Build frontend
print_status "Building frontend..."
cd frontend
npm install
npm run build
cd ..

print_success "Frontend built successfully!"

# Setup backend
print_status "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

cd ..

print_success "Backend setup completed!"

# Build Electron app
print_status "Building Electron application..."

# Determine platform
PLATFORM=$(uname -s)
case $PLATFORM in
    Darwin*)
        print_status "Building for macOS..."
        npm run dist-mac
        ;;
    Linux*)
        print_status "Building for Linux..."
        npm run dist-linux
        ;;
    MINGW*|CYGWIN*|MSYS*)
        print_status "Building for Windows..."
        npm run dist-win
        ;;
    *)
        print_warning "Unknown platform: $PLATFORM. Building for current platform..."
        npm run dist
        ;;
esac

print_success "Desktop application built successfully!"

# Show build output location
if [ -d "dist" ]; then
    print_status "Build output location: $(pwd)/dist"
    print_status "Available builds:"
    ls -la dist/
else
    print_warning "Build directory not found. Check for build errors above."
fi

print_success "🎉 Build process completed!"
print_status "You can find the built application in the 'dist' directory."