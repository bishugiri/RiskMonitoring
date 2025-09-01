#!/usr/bin/env python3
"""
Installation script for the Risk Monitor tool
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print installation banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                RISK MONITORING TOOL INSTALLER                ║
║                                                              ║
║  Setting up your risk monitoring environment...              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def setup_virtual_environment():
    """Set up a virtual environment"""
    print("\n🔧 Setting up virtual environment...")
    
    venv_dir = "venv"
    
    # Check if venv already exists
    if os.path.exists(venv_dir):
        print("✅ Virtual environment already exists")
        return True
    
    try:
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        print(f"✅ Virtual environment created at {venv_dir}")
        return True
    except Exception as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def install_dependencies(dev_mode=False):
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Determine the pip executable
    if os.path.exists("venv"):
        if sys.platform == "win32":
            pip_executable = os.path.join("venv", "Scripts", "pip")
        else:
            pip_executable = os.path.join("venv", "bin", "pip")
    else:
        pip_executable = [sys.executable, "-m", "pip"]
    
    try:
        # Upgrade pip
        subprocess.run([pip_executable, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([pip_executable, "install", "-r", "requirements.txt"], check=True)
        
        if dev_mode:
            # Install development requirements if they exist
            if os.path.exists("requirements-dev.txt"):
                subprocess.run([pip_executable, "install", "-r", "requirements-dev.txt"], check=True)
        
        # Install the package in development mode
        subprocess.run([pip_executable, "install", "-e", "."], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["logs", "output"]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directory created: {directory}")
        except Exception as e:
            print(f"❌ Error creating directory {directory}: {e}")
            return False
    
    return True

def setup_configuration():
    """Set up configuration files"""
    print("\n⚙️ Setting up configuration...")
    
    # Create .streamlit directory if it doesn't exist
    streamlit_dir = ".streamlit"
    os.makedirs(streamlit_dir, exist_ok=True)
    
    # Check if secrets.toml exists
    secrets_file = os.path.join(streamlit_dir, "secrets.toml")
    if not os.path.exists(secrets_file):
        try:
            with open(secrets_file, "w") as f:
                f.write("# API Keys for Risk Monitoring Application\n")
                f.write("OPENAI_API_KEY = \"your_openai_api_key_here\"\n")
                f.write("SERPAPI_KEY = \"your_serpapi_key_here\"\n")
                f.write("PINECONE_API_KEY = \"your_pinecone_api_key_here\"\n")
            print(f"✅ Created {secrets_file}")
        except Exception as e:
            print(f"❌ Error creating {secrets_file}: {e}")
            return False
    else:
        print(f"✅ {secrets_file} already exists")
    
    # Create scheduler config if it doesn't exist
    scheduler_config = "scheduler_config.json"
    if not os.path.exists(scheduler_config):
        try:
            import json
            config = {
                "run_time": "08:00",
                "timezone": "US/Eastern",
                "articles_per_entity": 5,
                "entities": [
                    "Apple Inc",
                    "Microsoft Corporation",
                    "Goldman Sachs",
                    "JPMorgan Chase",
                    "Bank of America"
                ],
                "keywords": [
                    "risk",
                    "financial",
                    "market",
                    "crisis",
                    "volatility"
                ],
                "use_openai": True
            }
            with open(scheduler_config, "w") as f:
                json.dump(config, f, indent=4)
            print(f"✅ Created {scheduler_config}")
        except Exception as e:
            print(f"❌ Error creating {scheduler_config}: {e}")
            return False
    else:
        print(f"✅ {scheduler_config} already exists")
    
    return True

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETE!")
    print("="*60)
    
    print("\n📋 Next steps:")
    
    print("\n1. Configure your API keys:")
    print("   • Edit .streamlit/secrets.toml")
    print("   • Add your OpenAI API key")
    print("   • Add your SerpAPI key")
    print("   • Add your Pinecone API key (if using vector DB)")
    
    print("\n2. Run the Streamlit app:")
    if sys.platform == "win32":
        print("   • venv\\Scripts\\activate")
    else:
        print("   • source venv/bin/activate")
    print("   • python -m risk_monitor.scripts.run_streamlit")
    
    print("\n3. Run the scheduler:")
    if sys.platform == "win32":
        print("   • venv\\Scripts\\activate")
    else:
        print("   • source venv/bin/activate")
    print("   • python -m risk_monitor.scripts.run_scheduler --setup")
    print("   • python -m risk_monitor.scripts.run_scheduler --run-now")
    
    print("\n📚 For more information:")
    print("   • Read the README.md file")
    
    print("\n⚠️  Important notes:")
    print("   • The free SerpAPI tier includes 100 searches per month")
    print("   • Results are saved in the output/ directory")
    print("   • Logs are written to logs/ directory")

def main():
    """Main installation function"""
    print_banner()
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Virtual Environment Setup", setup_virtual_environment),
        ("Dependencies Installation", install_dependencies),
        ("Directory Creation", create_directories),
        ("Configuration Setup", setup_configuration),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n{'-' * 50}")
        print(f"Step: {step_name}")
        print(f"{'-' * 50}")
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n❌ Installation failed. The following steps failed:")
        for step in failed_steps:
            print(f"   • {step}")
        print("\nPlease fix the issues above and run installation again.")
        return False
    else:
        print_next_steps()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
