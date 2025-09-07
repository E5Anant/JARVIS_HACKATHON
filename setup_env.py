import os
import sys
import platform
import re
from pathlib import Path

def setup_env_variables():
    """Create a .env file with required environment variables."""
    print("\n=== JARVIS-IV Environment Setup ===\n")
    
    # Determine where to store the .env file
    if getattr(sys, 'frozen', False):
        # We're running in a PyInstaller bundle
        base_dir = Path(os.path.dirname(sys.executable))
    else:
        # We're running in a normal Python environment
        base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    env_file = base_dir / '.env'
    
    # Check if .env already exists
    if env_file.exists():
        print(f"An existing .env file was found at {env_file}")
        overwrite = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled. Using existing environment variables.")
            return
    
    print("Setting up environment variables for JARVIS-IV...\n")
    
    # Collect required information
    env_vars = {}
    
    # Get API key
    print("\nGEMINI API KEY")
    print("You need a Google Gemini API key to use JARVIS-IV.")
    print("If you don't have one, visit: https://aistudio.google.com/app/apikey")
    env_vars['GEMINI_API_KEY'] = input("Enter your Gemini API key: ").strip()
    
    # Get user information
    print("\nPERSONALIZATION")
    env_vars['UserName'] = input("Enter your name (JARVIS will use this to address you): ").strip()
    
    while True:
        age_input = input("Enter your age: ").strip()
        if age_input.isdigit():
            env_vars['Age'] = age_input
            break
        else:
            print("Please enter a valid number for age.")
    
    # Assistant name
    print("\nASSISTANT CONFIGURATION")
    default_name = "JARVIS"
    custom_name = input(f"Enter assistant name (default: {default_name}): ").strip()
    env_vars['AssistantName'] = custom_name if custom_name else default_name
    
    # Write the .env file
    try:
        with open(env_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"\nEnvironment variables successfully saved to {env_file}")
        print("\nJARVIS-IV is now configured and ready to use!")
        
        # Platform-specific instructions
        system = platform.system()
        if system == "Windows":
            print("\nTo run JARVIS-IV:")
            print("- Double-click main.py, or")
            print("- Open a command prompt and run: python main.py")
        elif system == "Darwin":  # macOS
            print("\nTo run JARVIS-IV:")
            print("- Open Terminal and navigate to this directory")
            print("- Run: python3 main.py")
        else:  # Linux
            print("\nTo run JARVIS-IV:")
            print("- Open Terminal and navigate to this directory")
            print("- Run: python3 main.py")
        
    except Exception as e:
        print(f"Error writing environment variables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    setup_env_variables()
