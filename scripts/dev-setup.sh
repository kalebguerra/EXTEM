#!/bin/bash
# Development setup script for AI Image Generator Manager

set -e

echo "🔧 Setting up AI Image Generator Manager for development..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
print_status "Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    print_error "Node.js version 16+ is required. Current version: $(node --version)"
    exit 1
fi

print_success "Node.js $(node --version) found"

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
else
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version | cut -d' ' -f2 | cut -d'.' -f1-2)
fi

print_success "Python $PYTHON_VERSION found"

# Check MongoDB (optional)
if command -v mongod &> /dev/null; then
    print_success "MongoDB found"
else
    print_warning "MongoDB not found. You'll need to set up a MongoDB connection."
fi

# Install root dependencies
print_status "Installing root dependencies..."
npm install

# Setup frontend
print_status "Setting up frontend..."
cd frontend
npm install
cd ..

print_success "Frontend dependencies installed"

# Setup backend
print_status "Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating backend .env file..."
    cat > .env << EOL
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=ai_generator

# API Keys (replace with your actual keys)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=true

# Security
SECRET_KEY=your_secret_key_here
EOL
    print_warning "Created .env file with default values. Please update with your actual API keys."
fi

cd ..

# Setup frontend environment
if [ ! -f "frontend/.env" ]; then
    print_status "Creating frontend .env file..."
    cat > frontend/.env << EOL
REACT_APP_BACKEND_URL=http://localhost:8001
GENERATE_SOURCEMAP=false
DISABLE_ESLINT_PLUGIN=true
SKIP_PREFLIGHT_CHECK=true
EOL
fi

# Create development scripts
print_status "Creating development scripts..."

# Create start script
cat > start-dev.sh << 'EOL'
#!/bin/bash
echo "🚀 Starting AI Image Generator Manager in development mode..."

# Function to cleanup background processes
cleanup() {
    echo "Cleaning up..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting backend server..."
cd backend
source venv/bin/activate
python server.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting frontend development server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

# Start Electron in development mode
echo "Starting Electron application..."
npm run electron-dev &
ELECTRON_PID=$!

# Wait for all processes
wait
EOL

chmod +x start-dev.sh

print_success "Development environment setup completed!"

print_status "📋 Next steps:"
echo "1. Update backend/.env with your actual API keys"
echo "2. Make sure MongoDB is running (if using local MongoDB)"
echo "3. Run './start-dev.sh' to start the development environment"
echo "4. Or run individual components:"
echo "   - Backend: cd backend && source venv/bin/activate && python server.py"
echo "   - Frontend: cd frontend && npm start"
echo "   - Electron: npm run electron-dev"

print_success "🎉 Setup completed! Happy coding!"