#!/usr/bin/env python3
import json
import sys
import os
import logging
import getpass
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/fb_api_installer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fb_api_installer")

def modify_claude_config():
    """Modify the Claude desktop config JSON file."""
    try:
        # Get the current username - don't use root even when script runs with sudo
        username = os.environ.get('SUDO_USER') or os.environ.get('USER') or getpass.getuser()
        
        # For macOS package installations, try to get the console user if running as root
        if username == 'root' and sys.platform == 'darwin':
            try:
                result = subprocess.run(['stat', '-f', '%Su', '/dev/console'], 
                                       capture_output=True, text=True, check=True)
                console_user = result.stdout.strip()
                if console_user:
                    username = console_user
                    logger.info(f"Detected console user: {username}")
            except Exception as e:
                logger.warning(f"Failed to get console user: {e}")
        
        logger.info(f"Using username: {username}")
        
        # Set the correct config path
        target_config_path = f"/Users/{username}/Library/Application Support/Claude/claude_desktop_config.json"
        
        logger.info(f"Target config path: {target_config_path}")
        
        # Create directory if it doesn't exist
        config_dir = os.path.dirname(target_config_path)
        if config_dir and not os.path.exists(config_dir):
            logger.info(f"Creating directory: {config_dir}")
            os.makedirs(config_dir, mode=0o755, exist_ok=True)
        
        # Load existing config or create new one
        if os.path.exists(target_config_path):
            logger.info(f"Loading existing config file from {target_config_path}")
            with open(target_config_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Existing config is invalid JSON. Creating new config.")
                    data = {}
        else:
            logger.info(f"Config file not found. Creating new config.")
            data = {}

        # Define installation paths
        installation_path = "/Applications/FB-API-MCP-Server"
        
        # Create a wrapper shell script for Claude to call
        wrapper_script_path = os.path.join(installation_path, "run_server.sh")
        logger.info(f"Creating wrapper script at: {wrapper_script_path}")
        
        # The contents of the wrapper script
        wrapper_content = """#!/bin/bash
cd /Applications/FB-API-MCP-Server
source ./venv/bin/activate
python server.py
"""
        
        # Write the wrapper script
        with open(wrapper_script_path, 'w') as f:
            f.write(wrapper_content)
        
        # Make it executable
        os.chmod(wrapper_script_path, 0o755)
        logger.info(f"Made wrapper script executable")
        
        # Define fb-mcp-server configuration using the wrapper script
        fb_mcp_config = {
            "command": "/bin/bash",
            "args": [wrapper_script_path]
        }
        
        logger.info(f"Using command: {fb_mcp_config['command']}")
        logger.info(f"Using args: {fb_mcp_config['args']}")
        
        # Check if mcpServers exists and update accordingly
        if "mcpServers" in data:
            logger.info("mcpServers property exists, updating fb-mcp-server config")
            data["mcpServers"]["fb-mcp-server"] = fb_mcp_config
        else:
            logger.info("mcpServers property doesn't exist, creating it with fb-mcp-server config")
            data["mcpServers"] = {"fb-mcp-server": fb_mcp_config}
        
        # Save the updated config
        logger.info(f"Saving updated config to: {target_config_path}")
        with open(target_config_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        logger.info("Configuration update complete.")
        
        # Also create a launch agent plist to run server at login (optional)
        try:
            plist_path = f"/Users/{username}/Library/LaunchAgents/ai.gomarble.fbapimcpserver.plist"
            logger.info(f"Creating launch agent at: {plist_path}")
            
            plist_dir = os.path.dirname(plist_path)
            if not os.path.exists(plist_dir):
                os.makedirs(plist_dir, mode=0o755, exist_ok=True)
                
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.gomarble.fbapimcpserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{wrapper_script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{installation_path}</string>
    <key>StandardOutPath</key>
    <string>/tmp/fbapimcpserver.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/fbapimcpserver.error.log</string>
</dict>
</plist>"""
            
            with open(plist_path, 'w') as f:
                f.write(plist_content)
                
            # Set correct permissions
            os.chmod(plist_path, 0o644)
            
            # Load the launch agent
            try:
                subprocess.run(['launchctl', 'load', plist_path], check=True)
                logger.info("LaunchAgent loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load LaunchAgent: {e}")
                
        except Exception as e:
            logger.warning(f"Failed to create launch agent: {e}")
            # This is optional, so continue even if it fails
        
        return 0  # Success
    
    except Exception as e:
        logger.error(f"Error modifying config file: {str(e)}", exc_info=True)
        return 1  # Failure

if __name__ == "__main__":
    logger.info("Starting configuration modification script")
    exit_code = modify_claude_config()
    logger.info(f"Configuration script completed with exit code: {exit_code}")
    sys.exit(exit_code) 