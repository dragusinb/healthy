#!/usr/bin/env python3
"""
Create a clean deployment package of the Healthy app without any user data.
"""
import os
import shutil
import zipfile
from datetime import datetime

# Directories to exclude
EXCLUDE_DIRS = {
    '__pycache__',
    'node_modules',
    '.git',
    '.venv',
    'venv',
    'data',
    'uploads',
    'dist',  # Will rebuild on deploy
    '.pytest_cache',
    '.mypy_cache',
    'deploy_package',
    '.claude',
}

# File patterns to exclude
EXCLUDE_FILES = {
    '.env',
    '.env.local',
    '.env.production',
    '*.db',
    '*.sqlite',
    '*.sqlite3',
    '*.pyc',
    '*.pyo',
    '.DS_Store',
    'Thumbs.db',
    '*.log',
}

# Files to include as templates
TEMPLATE_FILES = {
    'backend_v2/.env.example': """# Backend Environment Variables
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://healthy:your_password@localhost/healthy
SECRET_KEY=your_secret_key_here_generate_with_openssl_rand_hex_32
FERNET_KEY=your_fernet_key_here_generate_with_python

# For Fernet key generation, run:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
""",
    'frontend_v2/.env.example': """# Frontend Environment Variables
VITE_API_URL=https://your-domain.com
""",
}

def should_exclude(path, name):
    """Check if a file or directory should be excluded."""
    # Check directory exclusions
    if name in EXCLUDE_DIRS:
        return True

    # Check file pattern exclusions
    for pattern in EXCLUDE_FILES:
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True

    return False

def create_package():
    source_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_name = f'healthy_deploy_{timestamp}'
    output_dir = os.path.join(source_dir, 'deploy_package')
    package_dir = os.path.join(output_dir, package_name)

    # Clean and create output directory
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir, exist_ok=True)

    print(f"Creating deployment package in: {package_dir}")

    # Copy files
    for root, dirs, files in os.walk(source_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(root, d)]

        # Calculate relative path
        rel_root = os.path.relpath(root, source_dir)
        if rel_root == '.':
            rel_root = ''

        # Skip the deploy_package directory itself
        if 'deploy_package' in rel_root:
            continue

        # Create target directory
        target_dir = os.path.join(package_dir, rel_root)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # Copy files
        for file in files:
            if should_exclude(root, file):
                continue

            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_dir, file)

            try:
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                print(f"  Warning: Could not copy {src_file}: {e}")

    # Create template files
    for template_path, content in TEMPLATE_FILES.items():
        full_path = os.path.join(package_dir, template_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"  Created template: {template_path}")

    # Create INSTALL.md
    install_guide = """# Healthy - Installation Guide

## Prerequisites
- Ubuntu 22.04+ or similar Linux distribution
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Nginx

## Server Setup

### 1. System Packages
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql nginx xvfb
```

### 2. Database Setup
```bash
sudo -u postgres psql
CREATE DATABASE healthy;
CREATE USER healthy WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE healthy TO healthy;
\\q
```

### 3. Backend Setup
```bash
cd /opt/healthy/backend_v2
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps

# Copy and edit environment file
cp .env.example .env
nano .env  # Add your API keys and database URL

# Initialize database
python -c "from database import engine, Base; Base.metadata.create_all(engine)"
```

### 4. Frontend Setup
```bash
cd /opt/healthy/frontend_v2
npm install
cp .env.example .env.production
nano .env.production  # Set your API URL
npm run build
```

### 5. Systemd Service
Create `/etc/systemd/system/healthy-api.service`:
```ini
[Unit]
Description=Healthy API Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/healthy/backend_v2
Environment="PATH=/opt/healthy/backend_v2/venv/bin"
ExecStart=/opt/healthy/backend_v2/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable healthy-api
sudo systemctl start healthy-api
```

### 6. Nginx Configuration
Create `/etc/nginx/sites-available/healthy`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /opt/healthy/frontend_v2/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~ ^/(auth|users|dashboard|documents|health|biomarkers|admin|evolution)(/|$) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/healthy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 8. Create Admin User
```bash
cd /opt/healthy/backend_v2
source venv/bin/activate
python -c "
from database import SessionLocal, engine
from models import User, Base
from auth.security import get_password_hash

Base.metadata.create_all(engine)
db = SessionLocal()
admin = User(
    email='admin@example.com',
    hashed_password=get_password_hash('your_password'),
    is_admin=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"
```

## Verification
1. Check API: `curl https://your-domain.com/health`
2. Open browser: `https://your-domain.com`
3. Login with admin credentials

## Troubleshooting
- Check API logs: `journalctl -u healthy-api -f`
- Check Nginx logs: `tail -f /var/log/nginx/error.log`
- Database connection: `PGPASSWORD=xxx psql -h localhost -U healthy -d healthy`
"""

    install_path = os.path.join(package_dir, 'INSTALL.md')
    with open(install_path, 'w') as f:
        f.write(install_guide)
    print("  Created INSTALL.md")

    # Create ZIP file
    zip_path = os.path.join(output_dir, f'{package_name}.zip')
    print(f"\nCreating ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)

    # Get size
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"\nPackage created successfully!")
    print(f"  Location: {zip_path}")
    print(f"  Size: {size_mb:.2f} MB")

    # Cleanup temporary directory
    shutil.rmtree(package_dir)
    print(f"\nCleaned up temporary files.")

    return zip_path

if __name__ == '__main__':
    create_package()
