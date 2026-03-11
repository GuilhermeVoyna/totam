#!/bin/bash
# install_totam.sh
# Script de instalação do TOTAM MQTT Controller no host

set -e

# =========================
# CONFIGURAÇÃO
# =========================
INSTALL_DIR="/opt/totam"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_FILE="/etc/systemd/system/totam.service"
USER_NAME=$(whoami)   # Usuário que vai possuir o venv

# =========================
# CRIAR DIRETÓRIO
# =========================
echo "Criando diretório $INSTALL_DIR..."
sudo mkdir -p $INSTALL_DIR
sudo chown -R $USER_NAME:$USER_NAME $INSTALL_DIR

# =========================
# CRIAR VENV
# =========================
echo "Criando virtual environment em $VENV_DIR..."
python3 -m venv $VENV_DIR

echo "Ativando venv e instalando dependências..."
source $VENV_DIR/bin/activate
pip install --upgrade pip
if [ -f "./requirements.txt" ]; then
    pip install -r ./requirements.txt
else
    echo "Atenção: requirements.txt não encontrado. Instalação de dependências ignorada."
fi
deactivate

# =========================
# COPIAR CÓDIGO E .ENV
# =========================
echo "Copiando código para $INSTALL_DIR..."
cp ./TOTAM.py $INSTALL_DIR/
cp ./.env $INSTALL_DIR/

# =========================
# CRIAR SERVICE SYSTEMD
# =========================
echo "Criando serviço systemd em $SERVICE_FILE..."
sudo tee $SERVICE_FILE > /dev/null <<EOL
[Unit]
Description=TOTAM MQTT Controller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/TOTAM.py
Restart=on-failure
RestartSec=10
EnvironmentFile=$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOL

# =========================
# ATIVAR E INICIAR SERVICE
# =========================
echo "Recarregando systemd e iniciando serviço..."
sudo systemctl daemon-reload
sudo systemctl enable totam.service
sudo systemctl start totam.service

echo "Instalação completa! Status do serviço:"
systemctl status totam.service --no-pager