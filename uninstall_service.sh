#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="switchbot-dashboard.service"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}"

echo "=== Uninstall switchbot-dashboard systemd service ==="
echo "Service: ${SERVICE_NAME}"
echo "Service file path: ${SYSTEMD_PATH}"
echo

# 停止（存在しなくても落ちないように）
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}"; then
  if systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "Stopping service..."
    sudo systemctl stop "${SERVICE_NAME}"
  else
    echo "Service is not active."
  fi

  echo "Disabling service..."
  # disableは存在しないと失敗するのでガード
  sudo systemctl disable "${SERVICE_NAME}" || true
else
  echo "Service unit file is not registered (may already be removed)."
fi

echo

# サービスファイル削除
if [[ -f "${SYSTEMD_PATH}" ]]; then
  echo "Removing service file..."
  sudo rm -f "${SYSTEMD_PATH}"
  echo "Removed: ${SYSTEMD_PATH}"
else
  echo "Service file not found: ${SYSTEMD_PATH}"
fi

echo

# systemdへ反映
echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl daemon-reexec

echo
echo "=== Check (should show nothing) ==="
systemctl list-unit-files | grep switchbot || true

echo
echo "Done."
