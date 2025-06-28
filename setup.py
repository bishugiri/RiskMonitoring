#!/usr/bin/env python3
"""
Setup script for the Risk Monitoring Tool
Helps users install dependencies and configure the tool
"""

import os
import sys
import subprocess
import shutil

def print_banner():
    """Print setup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                RISK MONITORING TOOL SETUP                    ║
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

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Check if pip is available
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pip is not available. Please install pip first.")
        return False
    
    try:
        # Install requirements
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install dependencies:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    print("\n🔧 Setting up configuration...")
    
    env_file = ".env"
    example_file = "env_example.txt"
    
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return True
    
    if not os.path.exists(example_file):
        print("❌ env_example.txt not found")
        return False
    
    try:
        # Copy example to .env
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from template")
        print("   Please edit .env and add your SerpAPI key")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def create_output_directory():
    """Create output directory"""
    print("\n📁 Creating output directory...")
    
    output_dir = "output"
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ Output directory created: {output_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        return False

def run_tests():
    """Run the test suite"""
    print("\n🧪 Running tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_tool.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 Next steps:")
    print("1. Get your SerpAPI API key:")
    print("   • Visit: https://serpapi.com/")
    print("   • Sign up for a free account")
    print("   • Copy your API key")
    
    print("\n2. Configure your API key:")
    print("   • Edit the .env file")
    print("   • Replace 'your_serpapi_key_here' with your actual key")
    
    print("\n3. Run the tool:")
    print("   • Basic usage: python main.py")
    print("   • Custom query: python main.py --query 'market crash'")
    print("   • More articles: python main.py --num-articles 20")
    
    print("\n📚 For more information:")
    print("   • Read the README.md file")
    print("   • Check the example outputs in the output/ directory")
    
    print("\n⚠️  Important notes:")
    print("   • The free SerpAPI tier includes 100 searches per month")
    print("   • Results are saved in the output/ directory")
    print("   • Logs are written to risk_monitor.log")

def main():
    """Main setup function"""
    print_banner()
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Create Configuration", create_env_file),
        ("Create Output Directory", create_output_directory),
        ("Run Tests", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n❌ Setup failed. The following steps failed:")
        for step in failed_steps:
            print(f"   • {step}")
        print("\nPlease fix the issues above and run setup again.")
        return False
    else:
        print_next_steps()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 