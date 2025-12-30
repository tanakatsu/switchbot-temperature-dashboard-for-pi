#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="switchbot-dashboard.service"
SYSTEMD_DIR="/etc/systemd/system"
SYSTEMD_PATH="${SYSTEMD_DIR}/${SERVICE_NAME}"

# 1. スクリプトを実行したディレクトリをWorkingDirectoryとする
WORKDIR="$(pwd)"

# 2. dockerとuvのパスをwhichで確認する
DOCKER_PATH="$(command -v docker || true)"
UV_PATH="$(command -v uv || true)"

if [[ -z "${DOCKER_PATH}" ]]; then
  echo "[ERROR] docker が見つかりません。docker をインストールしてから再実行してください。"
  exit 1
fi

if [[ -z "${UV_PATH}" ]]; then
  echo "[ERROR] uv が見つかりません。uv をインストールしてから再実行してください。"
  exit 1
fi

# docker compose サブコマンドの確認（念のため）
if ! "${DOCKER_PATH}" compose version >/dev/null 2>&1; then
  echo "[ERROR] 'docker compose' が利用できません。Docker Compose v2 を有効化してください。"
  exit 1
fi

# 3. ユーザー確認用にWorkingDirectoryとdocker、uvのパスを表示する
echo "=== Install switchbot-dashboard systemd service ==="
echo "WorkingDirectory: ${WORKDIR}"
echo "docker path      : ${DOCKER_PATH}"
echo "uv path          : ${UV_PATH}"
echo

# 追加の軽いチェック（任意だが親切）
if [[ ! -f "${WORKDIR}/main.py" ]]; then
  echo "[WARN] ${WORKDIR}/main.py が見つかりません（WorkingDirectoryが正しいか確認してください）"
fi

# docker compose ファイルの存在チェック（typoに気づけるように）
if [[ ! -f "${WORKDIR}/docker-compose.yml" && ! -f "${WORKDIR}/compose.yml" ]]; then
  echo "[WARN] docker-compose.yml / compose.yml が見つかりません。ファイル名を確認してください。"
fi
echo

# 4. systemd サービスファイル（switchbot-dashboard.service）を作成
TMP_SERVICE="$(mktemp)"
cat > "${TMP_SERVICE}" <<EOF
[Unit]
Description=SwitchBot Temperature Dashboard
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=${SUDO_USER:-$USER}
WorkingDirectory=${WORKDIR}

# Docker Compose 起動（無ければ作成、あれば起動/維持）
ExecStartPre=${DOCKER_PATH} compose up -d

# Python アプリ起動
ExecStart=${UV_PATH} run main.py

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Generated service file (temp): ${TMP_SERVICE}"
echo

# 5. サービスファイルを/etc/systemd/system にコピー（上書き）
echo "Copying service file to: ${SYSTEMD_PATH}"
sudo cp -f "${TMP_SERVICE}" "${SYSTEMD_PATH}"
sudo chmod 644 "${SYSTEMD_PATH}"

# 6. ユーザー確認用にコピー後のサービスファイルのパスを出力
echo "Installed service file: ${SYSTEMD_PATH}"
echo

# 7. systemd に反映
echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl daemon-reexec
echo

# 8. 自動起動を有効化
echo "Enabling service on boot..."
sudo systemctl enable "${SERVICE_NAME}"
echo

# 9. サービスが起動してない場合、手動起動してステータス確認
if ! systemctl is-active --quiet "${SERVICE_NAME}"; then
  echo "Service is not active. Starting now..."
  sudo systemctl start "${SERVICE_NAME}"
else
  echo "Service is already active."
fi

echo
echo "=== Service status ==="
systemctl status "${SERVICE_NAME}" --no-pager -l

# 後片付け
rm -f "${TMP_SERVICE}"

echo
echo "Done."
echo "Logs: journalctl -u ${SERVICE_NAME} -f"
