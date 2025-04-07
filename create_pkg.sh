#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
APP_NAME="FB-API-MCP-Server"
VERSION="1.0.0"
IDENTIFIER="ai.gomarble.fbapimcpserver"
INSTALL_ROOT="/Applications"
COMPONENT_PATH="$INSTALL_ROOT/$APP_NAME"
BUILD_ROOT="./pkg_build_root"
SCRIPTS_DIR="./scripts"
OUTPUT_PKG="./$APP_NAME-$VERSION.pkg"

# --- Ensure scripts directory exists ---
mkdir -p "$SCRIPTS_DIR"

# --- Prepare Staging Area ---
echo "--- Preparing Staging Area ---"
rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT$COMPONENT_PATH"

echo "--- Copying Source Files ---"
# Copy the server code and dependencies
cp server.py "$BUILD_ROOT$COMPONENT_PATH/"
cp -r templates "$BUILD_ROOT$COMPONENT_PATH/" 2>/dev/null || true
cp -r static "$BUILD_ROOT$COMPONENT_PATH/" 2>/dev/null || true
cp requirements.txt "$BUILD_ROOT$COMPONENT_PATH/" 2>/dev/null || true

# Copy modify_config.py to the installation directory
cp "$SCRIPTS_DIR/modify_config.py" "$BUILD_ROOT$COMPONENT_PATH/"
chmod +x "$BUILD_ROOT$COMPONENT_PATH/modify_config.py"

# Create a script to set up the virtual environment during installation
cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash
# Log all output for debugging
exec > /tmp/fb_api_postinstall.log 2>&1

APP_PATH="/Applications/FB-API-MCP-Server"
VENV_PATH="$APP_PATH/venv"

echo "Starting postinstall script at $(date)"
echo "App path: $APP_PATH"

# Create application directory if it doesn't exist
if [ ! -d "$APP_PATH" ]; then
    echo "Creating app directory: $APP_PATH"
    mkdir -p "$APP_PATH"
fi

# Identify the latest Python version available on the system
echo "Checking for Python versions:"
find /usr/local/bin /usr/bin -name "python3.*" | sort -V
PYTHON_CMD=$(find /usr/local/bin /usr/bin -name "python3.*" | sort -V | tail -n 1)
if [ -z "$PYTHON_CMD" ]; then
    echo "Using default Python3"
    PYTHON_CMD="python3"
fi
echo "Selected Python command: $PYTHON_CMD"
$PYTHON_CMD --version

# Remove previous venv if it exists
if [ -d "$VENV_PATH" ]; then
    echo "Removing old virtual environment"
    rm -rf "$VENV_PATH"
fi

# Create virtual environment with latest Python
echo "Creating new virtual environment using $PYTHON_CMD"
$PYTHON_CMD -m venv "$VENV_PATH"

# Activate and install dependencies
echo "Activating virtual environment and installing dependencies"
source "$VENV_PATH/bin/activate"

# Show the Python version and path inside the venv
echo "Python version inside venv:"
python --version
echo "Python path inside venv: $(which python)"

# Show contents of requirements.txt
echo "Contents of requirements.txt:"
cat "$APP_PATH/requirements.txt"

if [ -f "$APP_PATH/requirements.txt" ]; then
    echo "Installing requirements from requirements.txt"
    pip install --upgrade pip
    # Add verbose output to see what's happening
    pip install -v --no-cache-dir -r "$APP_PATH/requirements.txt"
    
    # Verify installation succeeded
    echo "Verifying package installation:"
    pip list
    
    # Try importing the mcp module to verify it works
    echo "Testing mcp module import:"
    python -c "import mcp; print(f'MCP module found at: {mcp.__file__}')" || echo "Failed to import mcp module"
else
    # Install minimal dependencies if no requirements file
    echo "No requirements.txt found, installing minimal dependencies"
    pip install flask requests
fi

# Create a test script to verify imports
cat > "$APP_PATH/test_imports.py" << 'TESTEOF'
try:
    import mcp
    print(f"Successfully imported mcp module from {mcp.__file__}")
    from mcp.server.fastmcp import FastMCP
    print("Successfully imported FastMCP")
except ImportError as e:
    print(f"Import Error: {e}")
    import sys
    print(f"Python path: {sys.path}")
TESTEOF

echo "Testing imports:"
python "$APP_PATH/test_imports.py"

# Make server.py executable
echo "Making server.py executable"
chmod +x "$APP_PATH/server.py"

# Run the configuration script to modify Claude's JSON config
echo "Running modify_config.py to update Claude configuration"
python "$APP_PATH/modify_config.py"

# Set ownership to the console user
CONSOLE_USER=$(stat -f "%Su" /dev/console)
if [ -n "$CONSOLE_USER" ]; then
    echo "Setting ownership to $CONSOLE_USER"
    chown -R "$CONSOLE_USER" "$APP_PATH"
fi

echo "Creating a launch command wrapper"
cat > "$APP_PATH/run_server.command" << 'CMDEOF'
#!/bin/bash
APP_PATH="/Applications/FB-API-MCP-Server"
VENV_PATH="$APP_PATH/venv"
cd "$APP_PATH"
source "$VENV_PATH/bin/activate"
python server.py
CMDEOF

chmod +x "$APP_PATH/run_server.command"

echo "Postinstall script completed successfully at $(date)"
exit 0
EOF

# Make sure the postinstall script is executable
chmod +x "$SCRIPTS_DIR/postinstall"

# --- Build the Package ---
echo "--- Building Package ---"

pkgbuild --root "$BUILD_ROOT" \
         --install-location "/" \
         --identifier "$IDENTIFIER" \
         --version "$VERSION" \
         --scripts "$SCRIPTS_DIR" \
         "$OUTPUT_PKG"

echo "--- Cleaning Up Staging Area ---"
rm -rf "$BUILD_ROOT"

echo "--- Package Creation Complete ---"
echo "Installer created at: $OUTPUT_PKG"
echo "--- Script Finished ---"