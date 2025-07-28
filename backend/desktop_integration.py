# Desktop Integration Module for AI Image Generator Manager
# This module provides desktop-specific features and integrations

import os
import sys
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import platform
import psutil
from datetime import datetime

logger = logging.getLogger(__name__)

class DesktopIntegration:
    """
    Desktop integration features for the AI Image Generator Manager
    """
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.app_data_dir = self._get_app_data_directory()
        self.config_file = self.app_data_dir / "config.json"
        self.logs_dir = self.app_data_dir / "logs"
        self.cache_dir = self.app_data_dir / "cache"
        
        # Ensure directories exist
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_app_data_directory(self) -> Path:
        """Get the appropriate application data directory for the platform"""
        if self.platform == "windows":
            base_dir = Path(os.environ.get("APPDATA", ""))
        elif self.platform == "darwin":  # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and others
            base_dir = Path.home() / ".local" / "share"
        
        return base_dir / "AI Image Generator Manager"
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # CPU information
            cpu_info = {
                "count": psutil.cpu_count(),
                "usage": psutil.cpu_percent(interval=1),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percentage": memory.percent
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percentage": (disk.used / disk.total) * 100
            }
            
            # Network information
            network = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            return {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor()
                },
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "python_version": sys.version,
                "uptime": self._get_system_uptime()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {"error": str(e)}
    
    def _get_system_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            return time.time() - psutil.boot_time()
        except:
            return 0.0
    
    async def save_desktop_config(self, config: Dict[str, Any]) -> bool:
        """Save desktop-specific configuration"""
        try:
            config["last_updated"] = datetime.utcnow().isoformat()
            config["platform"] = self.platform
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Desktop config saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving desktop config: {str(e)}")
            return False
    
    async def load_desktop_config(self) -> Dict[str, Any]:
        """Load desktop-specific configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Desktop config loaded from {self.config_file}")
                return config
            else:
                # Return default config
                default_config = {
                    "window_size": {"width": 1400, "height": 900},
                    "window_position": {"x": 100, "y": 100},
                    "theme": "dark",
                    "auto_start": False,
                    "minimize_to_tray": True,
                    "notifications_enabled": True,
                    "auto_update": True,
                    "log_level": "INFO"
                }
                await self.save_desktop_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading desktop config: {str(e)}")
            return {}
    
    async def setup_auto_start(self, enable: bool = True) -> bool:
        """Setup application to start automatically with the system"""
        try:
            if self.platform == "windows":
                return await self._setup_windows_auto_start(enable)
            elif self.platform == "darwin":
                return await self._setup_macos_auto_start(enable)
            else:
                return await self._setup_linux_auto_start(enable)
        except Exception as e:
            logger.error(f"Error setting up auto start: {str(e)}")
            return False
    
    async def _setup_windows_auto_start(self, enable: bool) -> bool:
        """Setup Windows auto start using registry"""
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "AI Image Generator Manager"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    app_path = sys.executable
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                    logger.info("Windows auto start enabled")
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                        logger.info("Windows auto start disabled")
                    except FileNotFoundError:
                        pass  # Key doesn't exist, which is fine
            
            return True
        except Exception as e:
            logger.error(f"Error setting up Windows auto start: {str(e)}")
            return False
    
    async def _setup_macos_auto_start(self, enable: bool) -> bool:
        """Setup macOS auto start using LaunchAgent"""
        try:
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(exist_ok=True)
            
            plist_file = launch_agents_dir / "com.aimanager.desktop.plist"
            
            if enable:
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aimanager.desktop</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
                
                with open(plist_file, 'w') as f:
                    f.write(plist_content)
                
                # Load the launch agent
                subprocess.run(["launchctl", "load", str(plist_file)], check=True)
                logger.info("macOS auto start enabled")
            else:
                if plist_file.exists():
                    # Unload and remove the launch agent
                    subprocess.run(["launchctl", "unload", str(plist_file)], check=False)
                    plist_file.unlink()
                    logger.info("macOS auto start disabled")
            
            return True
        except Exception as e:
            logger.error(f"Error setting up macOS auto start: {str(e)}")
            return False
    
    async def _setup_linux_auto_start(self, enable: bool) -> bool:
        """Setup Linux auto start using .desktop file"""
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / "ai-image-generator-manager.desktop"
            
            if enable:
                desktop_content = f"""[Desktop Entry]
Type=Application
Name=AI Image Generator Manager
Comment=Advanced desktop application for AI image generation
Exec={sys.executable}
Icon=ai-image-generator-manager
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                
                with open(desktop_file, 'w') as f:
                    f.write(desktop_content)
                
                # Make executable
                desktop_file.chmod(0o755)
                logger.info("Linux auto start enabled")
            else:
                if desktop_file.exists():
                    desktop_file.unlink()
                    logger.info("Linux auto start disabled")
            
            return True
        except Exception as e:
            logger.error(f"Error setting up Linux auto start: {str(e)}")
            return False
    
    async def create_desktop_shortcut(self) -> bool:
        """Create desktop shortcut for the application"""
        try:
            if self.platform == "windows":
                return await self._create_windows_shortcut()
            elif self.platform == "darwin":
                return await self._create_macos_shortcut()
            else:
                return await self._create_linux_shortcut()
        except Exception as e:
            logger.error(f"Error creating desktop shortcut: {str(e)}")
            return False
    
    async def _create_windows_shortcut(self) -> bool:
        """Create Windows desktop shortcut"""
        try:
            import win32com.client
            
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "AI Image Generator Manager.lnk"
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.WorkingDirectory = str(Path(sys.executable).parent)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            logger.info("Windows desktop shortcut created")
            return True
        except Exception as e:
            logger.error(f"Error creating Windows shortcut: {str(e)}")
            return False
    
    async def _create_macos_shortcut(self) -> bool:
        """Create macOS desktop alias"""
        try:
            desktop = Path.home() / "Desktop"
            alias_path = desktop / "AI Image Generator Manager"
            
            # Create symbolic link
            if not alias_path.exists():
                alias_path.symlink_to(sys.executable)
                logger.info("macOS desktop alias created")
            
            return True
        except Exception as e:
            logger.error(f"Error creating macOS alias: {str(e)}")
            return False
    
    async def _create_linux_shortcut(self) -> bool:
        """Create Linux desktop shortcut"""
        try:
            desktop = Path.home() / "Desktop"
            desktop_file = desktop / "ai-image-generator-manager.desktop"
            
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=AI Image Generator Manager
Comment=Advanced desktop application for AI image generation
Exec={sys.executable}
Icon=ai-image-generator-manager
Terminal=false
Categories=Graphics;Photography;
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            desktop_file.chmod(0o755)
            logger.info("Linux desktop shortcut created")
            return True
        except Exception as e:
            logger.error(f"Error creating Linux shortcut: {str(e)}")
            return False
    
    async def get_app_logs(self, lines: int = 100) -> List[str]:
        """Get recent application logs"""
        try:
            log_files = list(self.logs_dir.glob("*.log"))
            if not log_files:
                return []
            
            # Get the most recent log file
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_log, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            logger.error(f"Error getting app logs: {str(e)}")
            return [f"Error reading logs: {str(e)}"]
    
    async def clear_cache(self) -> bool:
        """Clear application cache"""
        try:
            import shutil
            
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Application cache cleared")
                return True
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def export_data(self, export_path: str, include_logs: bool = False) -> bool:
        """Export application data for backup"""
        try:
            import zipfile
            
            export_file = Path(export_path)
            
            with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add config file
                if self.config_file.exists():
                    zipf.write(self.config_file, "config.json")
                
                # Add logs if requested
                if include_logs:
                    for log_file in self.logs_dir.glob("*.log"):
                        zipf.write(log_file, f"logs/{log_file.name}")
                
                # Add any other important files
                # This would be expanded based on what data needs to be backed up
            
            logger.info(f"Data exported to {export_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return False

# Global instance
desktop_integration = DesktopIntegration()