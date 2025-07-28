# AI Image Generator Manager - Desktop Application

Advanced desktop application for managing AI image generation across multiple platforms including OpenAI DALL-E, Midjourney, ImageFX, and more.

## 🚀 Features

### Core Features
- **Multi-Platform Support**: Integrate with OpenAI DALL-E, Midjourney, ImageFX, and other AI image generators
- **Intelligent Prompt Generation**: Use OpenAI GPT-4 or Google Gemini to generate creative prompts
- **Batch Processing**: Process multiple prompts across multiple providers simultaneously
- **Real-time Monitoring**: Live dashboard with WebSocket updates
- **Advanced Analytics**: Comprehensive performance metrics and reporting
- **Desktop Integration**: Native desktop features with system tray support

### Desktop-Specific Features
- **Native Desktop App**: Built with Electron for cross-platform compatibility
- **System Tray Integration**: Minimize to tray and quick access
- **Auto-Start**: Optional system startup integration
- **Desktop Notifications**: Native system notifications
- **File Operations**: Import/export prompts and results
- **Offline Capability**: Local data storage and caching
- **Auto-Updates**: Automatic application updates

### Advanced Features
- **Dynamic Selector Management**: Update automation selectors without code changes
- **Intelligent Rate Limiting**: Adaptive rate limiting based on provider performance
- **Error Recovery**: Advanced error handling with multiple fallback strategies
- **Smart Job Scheduling**: Optimize job execution based on provider performance
- **Comprehensive Logging**: Detailed logging and debugging capabilities

## 🛠 Technology Stack

### Frontend
- **React 19**: Modern React with hooks and context
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icon library
- **WebSocket**: Real-time communication

### Backend
- **FastAPI**: High-performance Python web framework
- **MongoDB**: Document database with Motor async driver
- **WebSocket**: Real-time bidirectional communication
- **Pydantic**: Data validation and serialization

### Desktop
- **Electron**: Cross-platform desktop application framework
- **Node.js**: JavaScript runtime for desktop features
- **Native APIs**: Platform-specific integrations

## 📦 Installation

### Prerequisites
- **Node.js 16+**: JavaScript runtime
- **Python 3.8+**: Backend runtime
- **MongoDB**: Database (local or cloud)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/ai-image-generator-manager.git
   cd ai-image-generator-manager
   ```

2. **Run the setup script**
   ```bash
   chmod +x scripts/dev-setup.sh
   ./scripts/dev-setup.sh
   ```

3. **Configure API keys**
   Edit `backend/.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   MONGO_URL=mongodb://localhost:27017
   ```

4. **Start development environment**
   ```bash
   ./start-dev.sh
   ```

### Manual Setup

1. **Install root dependencies**
   ```bash
   npm install
   ```

2. **Setup frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Setup backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cd ..
   ```

4. **Start services**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate
   python server.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   
   # Terminal 3 - Electron (after frontend starts)
   npm run electron-dev
   ```

## 🏗 Building for Production

### Build Desktop Application

```bash
# Build for current platform
npm run dist

# Build for specific platforms
npm run dist-win    # Windows
npm run dist-mac    # macOS
npm run dist-linux  # Linux
```

### Using Build Script

```bash
chmod +x scripts/build-desktop.sh
./scripts/build-desktop.sh
```

The built application will be available in the `dist` directory.

## 🔧 Configuration

### Backend Configuration (`backend/.env`)

```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=ai_generator

# API Keys
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key

# Server
HOST=0.0.0.0
PORT=8001
DEBUG=false

# Security
SECRET_KEY=your_secret_key
```

### Frontend Configuration (`frontend/.env`)

```env
REACT_APP_BACKEND_URL=http://localhost:8001
GENERATE_SOURCEMAP=false
```

## 📱 Usage

### 1. Dashboard
- Monitor active jobs and system health
- View real-time statistics
- Track recent activity

### 2. AI Prompt Generation
- Enter a theme or topic
- Choose AI provider (OpenAI or Gemini)
- Generate creative prompts
- Create image generation jobs

### 3. Batch Processing
- Upload multiple prompts
- Select multiple providers
- Monitor batch progress
- Download results

### 4. Provider Management
- Configure AI image generation providers
- Update automation selectors
- Monitor provider performance
- Adjust rate limits

### 5. Analytics
- View detailed performance metrics
- Analyze success rates
- Monitor error patterns
- Generate reports

## 🔌 API Endpoints

### Core Endpoints
- `GET /api/health` - System health status
- `GET /api/config` - Application configuration
- `POST /api/jobs` - Create image generation job
- `GET /api/jobs` - List jobs
- `POST /api/generate-prompts` - Generate AI prompts

### Desktop Endpoints
- `GET /api/desktop/system-info` - System information
- `GET /api/desktop/config` - Desktop configuration
- `POST /api/desktop/auto-start` - Setup auto-start
- `GET /api/desktop/logs` - Application logs

### WebSocket
- `WS /api/ws` - Real-time updates

## 🧪 Development

### Project Structure

```
ai-image-generator-manager/
├── frontend/                 # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/                  # FastAPI backend
│   ├── server.py
│   ├── advanced_features.py
│   ├── desktop_integration.py
│   └── requirements.txt
├── public/                   # Electron main process
│   ├── electron.js
│   ├── preload.js
│   └── splash.html
├── assets/                   # Application assets
├── scripts/                  # Build and setup scripts
├── installer/                # Installer configurations
└── package.json             # Root package.json
```

### Development Scripts

```bash
npm run start          # Start all services
npm run frontend       # Start frontend only
npm run backend        # Start backend only
npm run electron       # Start Electron only
npm run electron-dev   # Start Electron in development
```

### Testing

```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
source venv/bin/activate
pytest
```

## 🚀 Deployment

### Desktop Distribution

1. **Build the application**
   ```bash
   npm run dist
   ```

2. **Distribute the installer**
   - Windows: `.exe` installer in `dist/`
   - macOS: `.dmg` file in `dist/`
   - Linux: `.AppImage` file in `dist/`

### Auto-Updates

The application supports automatic updates using `electron-updater`. Configure your update server in the build configuration.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/your-repo/ai-generator/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-repo/ai-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/ai-generator/discussions)

## 🙏 Acknowledgments

- OpenAI for DALL-E and GPT-4 APIs
- Google for Gemini API
- Electron team for the desktop framework
- React and FastAPI communities

---

**AI Image Generator Manager** - Transform your AI image generation workflow with this powerful desktop application.
