#!/bin/bash
set -e

echo "Packaging project..."
tar --exclude='.venv' --exclude='node_modules' --exclude='.git' --exclude='.next' -czf /tmp/klar-poc-deploy.tar.gz -C /Users/adrianalfajri/Projects/klar-poc .

echo "Uploading to VM..."
gcloud compute scp /tmp/klar-poc-deploy.tar.gz klar-poc-vm:~ --project=molten-mechanic-395504 --zone=asia-southeast2-a --strict-host-key-checking=no

echo "Extracting and Deploying on VM..."
gcloud compute ssh klar-poc-vm --project=molten-mechanic-395504 --zone=asia-southeast2-a --command="mkdir -p ~/klar-poc && tar -xzf ~/klar-poc-deploy.tar.gz -C ~/klar-poc && cd ~/klar-poc/project && if [ -f ./stop.sh ]; then ./stop.sh; fi && cd ~/klar-poc/project/ui && npm install && npm run build && cd ~/klar-poc/project && ./start.sh"

echo "Deployment finished!"
