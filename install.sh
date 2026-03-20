#!/bin/bash
# install_totam.sh
# Script de instalação do TOTAM MQTT Controller

set -e

# =========================
# CONFIGURAÇÃO
# =========================
INSTALL_DIR="/opt/totam"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_FILE="/etc/systemd/system/totam.service"

# caminho de onde o script foi executado
REPO_PATH="$(pwd)"

echo "Instalando TOTAM..."
echo "Origem: $REPO_PATH"
echo "Destino: $INSTALL_DIR"

# =========================
# DEPENDÊNCIAS
# =========================
echo "Instalando dependências..."
apt update
apt install -y python3 python3-venv python3-pip git rsync

# =========================
# CRIAR DIRETÓRIO
# =========================
echo "Criando diretório..."
mkdir -p $INSTALL_DIR

# =========================
# COPIAR PROJETO
# =========================
echo "Sincronizando arquivos..."
rsync -av --delete \
  --exclude ".git" \
  --exclude ".gitignore" \
  --exclude "install.sh" \
  --exclude "README.md" \
  --exclude ".env.example" \
  "$REPO_PATH/" "$INSTALL_DIR/"

# =========================
# CRIAR VENV
# =========================
echo "Criando virtualenv..."
python3 -m venv $VENV_DIR

echo "Instalando dependências Python..."
$VENV_DIR/bin/pip install --upgrade pip

if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    $VENV_DIR/bin/pip install -r $INSTALL_DIR/requirements.txt
else
    echo "Aviso: requirements.txt não encontrado"
fi

# =========================
# CRIAR / ATUALIZAR .ENV
# =========================
ENV_FILE="$INSTALL_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Criando .env..."

    cat <<EOF > $ENV_FILE
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_BROKER=
MQTT_PORT=8883

GROUP=default

SHUTDOWN=shutdown
REBOOT=reboot
SLEEP=sleep

# caminho de origem (onde install foi executado)
REPO_PATH=$REPO_PATH

# caminho da instalação
UPDATE_PATH=$INSTALL_DIR

SERVICE_NAME=totam
EOF
else
    echo ".env já existe, mantendo configurações atuais"
fi

# =========================
# CRIAR SERVICE SYSTEMD
# =========================
echo "Criando serviço systemd..."

cat <<EOL > $SERVICE_FILE
[Unit]
Description=TOTAM MQTT Controller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR

EnvironmentFile=$INSTALL_DIR/.env

ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/app/main.py

Restart=always
RestartSec=5

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

# =========================
# ATIVAR SERVIÇO
# =========================
echo "Ativando serviço..."

systemctl daemon-reload
systemctl enable totam.service
systemctl restart totam.service

# =========================
# STATUS
# =========================
echo ""
echo "Instalação concluída!"
systemctl status totam.service --no-pager

echo ""
echo "Logs:"
echo "journalctl -u totam -f"