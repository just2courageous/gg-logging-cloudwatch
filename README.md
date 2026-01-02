# gg-logging-cloudwatch

Centralized logging on **AWS EKS** using **Fluent Bit → CloudWatch Logs** with **IRSA (OIDC)** (no static AWS keys).

## What this does
- Deploys **Fluent Bit** as a **DaemonSet** in the `logging` namespace
- Collects container logs from nodes
- Sends logs to **CloudWatch Logs** group: `/eks/gg/cluster`
- Uses **IAM Role for Service Account (IRSA)** so pods assume an IAM role securely

## Repo layout
- `logging/values.yaml` — Helm values (inputs/filters/outputs)
- `docs/screenshots/` — proof screenshots
- `fluentbit-trust.json` — IAM trust policy (OIDC → serviceaccount)
- `fluentbit-policy.json` — IAM permissions for CloudWatch Logs

## Key commands used
### Verify Fluent Bit is running
```bash
kubectl -n logging get ds fluent-bit
kubectl -n logging get pods -o wide
kubectl -n logging logs -l app.kubernetes.io/name=fluent-bit --tail=50
