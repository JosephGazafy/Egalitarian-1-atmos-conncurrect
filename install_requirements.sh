cat > install_requirements.sh <<'EOF'
#!/usr/bin/env bash
set -u

echo "======================================================="
echo " ATMOS-OMEGA / GCITS INSTALLER"
echo "======================================================="

PROJECT_DIR="$(pwd)"

echo "[INFO] Project directory: $PROJECT_DIR"

install_termux_packages() {
    if command -v pkg >/dev/null 2>&1; then
        echo "[INFO] Android/Termux-style environment detected."

        pkg update -y || true
        pkg upgrade -y || true

        pkg install -y \
            python \
            python-pip \
            git \
            curl \
            wget \
            unzip \
            zip \
            clang \
            make \
            cmake \
            openssl \
            libffi \
            nano \
            termux-tools || true
    else
        echo "[INFO] pkg not found. Skipping Termux package install."
    fi
}

install_python_packages() {
    echo "[INFO] Upgrading pip tools..."

    python3 -m pip install --upgrade pip setuptools wheel || true

    echo "[INFO] Installing safe Python requirements..."

    python3 -m pip install \
        requests \
        python-dateutil \
        pytz \
        tzdata \
        rich \
        colorama \
        click \
        pyyaml \
        tqdm || true

    echo "[INFO] Installing optional scientific packages..."

    python3 -m pip install \
        numpy \
        sympy \
        networkx \
        matplotlib || true

    echo "[INFO] Installing optional web packages..."

    python3 -m pip install \
        flask \
        fastapi \
        uvicorn \
        aiohttp \
        websockets || true
}

create_requirements_file() {
    echo "[INFO] Writing requirements.txt..."

    cat > requirements.txt <<'REQ'
requests
python-dateutil
pytz
tzdata
rich
colorama
click
pyyaml
tqdm
numpy
sympy
networkx
matplotlib
flask
fastapi
uvicorn
aiohttp
websockets
REQ
}

create_project_folders() {
    echo "[INFO] Creating project folders..."

    mkdir -p \
        outputs \
        logs \
        telemetry \
        reports \
        dashboards \
        exports \
        backups \
        omega_thought_outputs
}

create_run_script() {
    echo "[INFO] Creating run script..."

    cat > run_atmos_omega.sh <<'RUN'
#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

echo "Starting ATMOS-OMEGA / GCITS..."

if [ -f "main.py" ]; then
    python3 main.py
else
    echo "main.py not found."
    exit 1
fi
RUN

    chmod +x run_atmos_omega.sh
}

create_thought_run_script() {
    echo "[INFO] Creating thought hub run script..."

    cat > run_thought_hub.sh <<'RUN'
#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

echo "Starting Omega Thought Hub..."

if [ -f "omega_thought_controls.py" ]; then
    python3 omega_thought_controls.py
else
    echo "omega_thought_controls.py not found."
    exit 1
fi
RUN

    chmod +x run_thought_hub.sh
}

verify_install() {
    echo "[INFO] Verifying install..."

    python3 - <<'PY'
import sys
print("Python:", sys.version)

modules = [
    "json",
    "datetime",
    "http.server",
    "socketserver",
    "threading",
    "pathlib",
]

for m in modules:
    __import__(m)
    print("[OK]", m)

optional = [
    "requests",
    "dateutil",
    "pytz",
    "rich",
    "yaml",
    "numpy",
    "sympy",
    "networkx",
    "matplotlib",
    "flask",
]

for m in optional:
    try:
        __import__(m)
        print("[OK optional]", m)
    except Exception:
        print("[SKIP optional]", m)

print("Verification complete.")
PY
}

install_termux_packages
install_python_packages
create_requirements_file
create_project_folders
create_run_script
create_thought_run_script
verify_install

echo
echo "======================================================="
echo " INSTALL COMPLETE"
echo "======================================================="
echo
echo "Run main dashboard:"
echo "  ./run_atmos_omega.sh"
echo
echo "Run thought hub only:"
echo "  ./run_thought_hub.sh"
echo
echo "Or manually:"
echo "  python3 main.py"
echo "  python3 omega_thought_controls.py"
echo
EOF

chmod +x install_requirements.sh
./install_requirements.sh