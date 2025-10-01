#!/usr/bin/env python3
"""
Setup script for Bot Performance Dashboard
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Setup environment file"""
    env_file = Path('.env')
    env_example = Path('env_example.txt')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from env_example.txt")
        print("⚠️  Please edit .env file with your actual database credentials")
    else:
        print("❌ env_example.txt not found")
        return

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    os.system("pip install -r requirements.txt")
    print("✅ Requirements installed")

def create_directories():
    """Create necessary directories"""
    directories = ['api', 'backups', 'reports']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main setup function"""
    print("🤖 Bot Performance Dashboard Setup")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Install requirements
    install_requirements()
    
    # Create directories
    create_directories()
    
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Run: python manual_report_updater.py")
    print("3. Run: streamlit run static_dashboard.py")
    print("\nFor Vercel deployment:")
    print("1. Push code to GitHub")
    print("2. Connect to Vercel")
    print("3. Set environment variables in Vercel dashboard")

if __name__ == "__main__":
    main()
