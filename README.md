# ☁️ Kubernetes Penetration Testing & Benchmarking (KPTB)

> **A deliberately vulnerable ML application deployed into Kubernetes — paired with automated CIS benchmarking (kube-bench) and penetration testing (kube-hunter) to identify and document real cluster misconfigurations**
>
> An intentionally insecure Flask + XGBoost weather prediction app is containerised and deployed with excessive RBAC permissions, privileged containers, and host filesystem mounts — then systematically attacked using industry-standard Kubernetes security tooling to produce structured audit reports.

---

<div align="center">

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![XGBoost](https://img.shields.io/badge/Model-XGBoost-orange)](https://xgboost.readthedocs.io/)
[![Kubernetes](https://img.shields.io/badge/Platform-Kubernetes-326CE5?logo=kubernetes)](https://kubernetes.io/)
[![kube-bench](https://img.shields.io/badge/CIS-kube--bench-red)](https://github.com/aquasecurity/kube-bench)
[![kube-hunter](https://img.shields.io/badge/PenTest-kube--hunter-darkred)](https://github.com/aquasecurity/kube-hunter)
[![Flask](https://img.shields.io/badge/Serving-Flask-black?logo=flask)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

> ⚠️ **Security Disclaimer:** The Kubernetes manifests in this repository (`k8s-deployment.yaml`, `insecure-rbac.yaml`) are **intentionally misconfigured** for security research and learning. Never deploy these configurations to a production cluster.

---

## 📊 Project Slides

👉 **[View the Project Presentation (PPTX)](https://docs.google.com/presentation/d/1tn1jOqAXZa0jFQKfAsXQ3p_X33nGcZfC/edit?usp=sharing&ouid=117459468470211543781&rtpof=true&sd=true)**

---

## 📋 Table of Contents

| # | Section |
|---|---------|
| 1 | [Project Overview](#1-project-overview) |
| 2 | [Dual-Purpose Architecture](#2-dual-purpose-architecture) |
| 3 | [Tech Stack](#3-tech-stack) |
| 4 | [ML Component — Rain Prediction Model](#4-ml-component--rain-prediction-model) |
| 5 | [Repository Structure](#5-repository-structure) |
| 6 | [Kubernetes Security — Deliberate Vulnerabilities](#6-kubernetes-security--deliberate-vulnerabilities) |
| 7 | [kube-bench — CIS Benchmarking](#7-kube-bench--cis-benchmarking) |
| 8 | [kube-hunter — Penetration Testing](#8-kube-hunter--penetration-testing) |
| 9 | [kube-bench Report Generator](#9-kube-bench-report-generator) |
| 10 | [How to Replicate — Full Setup Guide](#10-how-to-replicate--full-setup-guide) |
| 11 | [Interpreting Security Results](#11-interpreting-security-results) |
| 12 | [Remediating the Vulnerabilities](#12-remediating-the-vulnerabilities) |
| 13 | [How to Improve This Project](#13-how-to-improve-this-project) |
| 14 | [Troubleshooting](#14-troubleshooting) |
| 15 | [Glossary](#15-glossary) |

---

## 1. Project Overview

This project serves two interconnected purposes:

**ML purpose:** Train an XGBoost binary classifier on the Australian weather dataset (145,460 records, 24 features) to predict whether it will rain tomorrow — achieving 86.6% test accuracy. Package the model into a Flask web app.

**Security purpose:** Deploy that Flask app into a Kubernetes cluster using intentionally misconfigured manifests, then run automated security audits to detect and document every misconfiguration — simulating how real vulnerabilities are discovered in enterprise K8s deployments.

| Aspect | Detail |
|--------|--------|
| **ML task** | Binary classification: will it rain tomorrow? (Yes/No) |
| **Dataset** | Australian weather dataset — 145,460 rows · 23 original columns |
| **Model** | XGBoostClassifier (default params) |
| **Train accuracy** | 89.7% |
| **Test accuracy** | 86.6% |
| **Serving** | Flask on port 5000 (HTML form → prediction) |
| **Deployment** | Kubernetes in namespace `vulnerable-test` |
| **Deliberate vulns** | 8 RBAC/container/mount misconfigurations |
| **CIS benchmark** | kube-bench against CIS Kubernetes Benchmark 1.23 |
| **Pen testing** | kube-hunter (pod-mode attack simulation) |
| **Report gen** | `kubebench-report-generator.py` → Markdown audit report |

---

## 2. Dual-Purpose Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ML PIPELINE (Target Application)               │
│                                                                     │
│  artifacts/raw/data.csv (145,460 rows)                             │
│         │                                                           │
│  DataProcessing:                                                    │
│    Date → Year/Month/Day · mean imputation · LabelEncoder          │
│    → X_train/X_test/y_train/y_test (.pkl)                          │
│         │                                                           │
│  ModelTraining:                                                     │
│    XGBClassifier().fit() · eval: accuracy/precision/recall/F1      │
│    → artifacts/models/model.pkl                                     │
│         │                                                           │
│  Flask (application.py):                                           │
│    GET/POST / → HTML form → model.predict() → Yes/No              │
│    → docker build → flask-app:latest                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│              KUBERNETES DEPLOYMENT (Deliberately Vulnerable)        │
│                                                                     │
│  Namespace: vulnerable-test                                         │
│                                                                     │
│  insecure-rbac.yaml:                                               │
│    ServiceAccount → ClusterRoleBinding (cluster-admin) ← ⚠️ VULN  │
│                                                                     │
│  k8s-deployment.yaml:                                              │
│    runAsUser: 0            ← root ⚠️                               │
│    privileged: true        ← ⚠️                                    │
│    hostPath: /             ← full host filesystem ⚠️               │
│    SECRET_PASSWORD in env  ← hardcoded secret ⚠️                  │
│    SYS_ADMIN, NET_ADMIN    ← excessive capabilities ⚠️            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                  KUBERNETES SECURITY TOOLING                        │
│                                                                     │
│  kube-bench (kube-bench.yaml):                                     │
│    aquasec/kube-bench:latest                                        │
│    --benchmark cis-1.23 --json                                      │
│    → kube-bench-results.json                                        │
│         │                                                           │
│  kubebench-report-generator.py:                                    │
│    JSON → structured Markdown report                                │
│    (per control: PASS/FAIL/WARN/INFO + remediation steps)          │
│                                                                     │
│  kube-hunter (kube-hunter.yaml):                                   │
│    aquasec/kube-hunter:0.6.8                                        │
│    kube-hunter --pod (attack from within the cluster)              │
│    → vulnerability report                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11 | Core language |
| **ML** | XGBoost + Scikit-learn | Gradient boosting classifier + preprocessing |
| **Data** | Pandas, NumPy | Data loading, EDA, feature engineering |
| **Serialisation** | joblib | Save/load model and split data pickles |
| **Web framework** | Flask | Serve prediction form + result |
| **Templating** | Jinja2 / HTML | Prediction form (index.html) + CSS (style.css) |
| **Containerisation** | Docker (`python:3.11`) | Build `flask-app:latest` image |
| **Orchestration** | Kubernetes | Deploy + expose Flask app in `vulnerable-test` namespace |
| **CIS Benchmarking** | kube-bench (Aqua Security) | Runs CIS Kubernetes Benchmark 1.23 checks |
| **Penetration Testing** | kube-hunter (Aqua Security) | Active attack simulation from within the pod |
| **Report generation** | Python `json` + `pathlib` | Converts kube-bench JSON → Markdown audit report |
| **Logging** | Python `logging` | Per-day log file in `logs/` |
| **Packaging** | `setup.py` | Installs project as `Kubernetes-Penetration-Testing-and-Benchmarking` |

---

## 4. ML Component — Rain Prediction Model

### Dataset

| Property | Detail |
|----------|--------|
| **Source** | Australian Bureau of Meteorology weather data |
| **Rows** | 145,460 daily weather observations |
| **Locations** | 49 Australian weather stations |
| **Date range** | 2007–2017 |
| **Target** | `RainTomorrow` — Yes/No binary classification |
| **After preprocessing** | 123,710 rows (rows with remaining NaN after imputation dropped) |

### Features (24 inputs to the model)

| Category | Features |
|----------|---------|
| **Temperature** | `MinTemp`, `MaxTemp`, `Temp9am`, `Temp3pm` |
| **Rain** | `Rainfall`, `RainToday` (label-encoded) |
| **Wind** | `WindGustDir`, `WindGustSpeed`, `WindDir9am`, `WindDir3pm`, `WindSpeed9am`, `WindSpeed3pm` |
| **Atmosphere** | `Humidity9am`, `Humidity3pm`, `Pressure9am`, `Pressure3pm`, `Evaporation`, `Sunshine` |
| **Sky** | `Cloud9am`, `Cloud3pm` |
| **Location/time** | `Location` (label-encoded, 49 stations), `Year`, `Month`, `Day` |

### Preprocessing Pipeline (`DataProcessing`)

1. **Date decomposition** — `Date` → `Year`, `Month`, `Day` (preserves temporal signals)
2. **Mean imputation** — all numerical columns filled with column mean (handles NaN in Evaporation, Sunshine, Cloud columns which have 40–50% missing)
3. **Drop remaining NA** — rows still missing after imputation dropped (primarily from categorical columns)
4. **Label encoding** — 6 categorical columns (`Location`, `WindGustDir`, `WindDir9am`, `WindDir3pm`, `RainToday`, `RainTomorrow`) encoded with `LabelEncoder`
5. **Train/test split** — 80/20, `random_state=42`

> **Note:** Label encoders are not saved — only the trained model is persisted as `model.pkl`. At inference time (`application.py`) the form expects pre-encoded integer values for categorical features.

### Model Performance

| Metric | Training | Test |
|--------|----------|------|
| **Accuracy** | **89.7%** | **86.6%** |
| Precision | — | logged |
| Recall | — | logged |
| F1 | — | logged |

The 3.1pp gap between train and test accuracy indicates mild overfitting — expected with default XGBoost parameters on a tabular weather dataset.

### Class Distribution

```
RainTomorrow
No     110,316  (77.6%)
Yes     32,877  (22.4%)
```

The dataset is imbalanced ~3.5:1 — `No rain` dominates. Default XGBoostClassifier handles this reasonably but class weights would improve minority class recall.

---

## 5. Repository Structure

```
Kubernetes-Penetration-Testing-and-Benchmarking/
│
├── src/                                  # ML pipeline components
│   ├── __init__.py
│   ├── logger.py                         # get_logger() — daily log file in logs/
│   ├── custom_exception.py               # CustomException with file + line traceback
│   ├── data_processing.py                # DataProcessing — load, impute, encode, split
│   └── model_training.py                 # ModelTraining — XGBoost fit, eval, save
│
├── pipeline/
│   └── training_pipeline.py              # Entry point — DataProcessing → ModelTraining
│
├── artifacts/
│   ├── raw/data.csv                      # Source: 145,460-row Australian weather data
│   ├── processed/                        # X_train/X_test/y_train/y_test .pkl files
│   └── models/model.pkl                  # Trained XGBoostClassifier
│
├── notebook/
│   └── notebook.ipynb                    # EDA + training research notebook
│
├── templates/
│   └── index.html                        # Flask prediction form (Jinja2)
│
├── static/
│   └── style.css                         # Form styling
│
├── application.py                        # Flask app — 24-feature form → Yes/No prediction
│
├── ── Kubernetes manifests ──────────────────────────────────────────
│
├── insecure-rbac.yaml                    # ⚠️  ServiceAccount + cluster-admin binding
├── k8s-deployment.yaml                   # ⚠️  Privileged pod with host filesystem mount
│
├── ── Security tooling ─────────────────────────────────────────────
│
├── kube-bench.yaml                       # CIS 1.23 benchmark Pod (aquasec/kube-bench)
├── kube-hunter.yaml                      # Pen test Job (aquasec/kube-hunter:0.6.8)
├── kubebench-report-generator.py         # JSON → Markdown audit report generator
│
├── Dockerfile                            # python:3.11 · pip install -e . · EXPOSE 5000
├── requirements.txt                      # pandas, numpy, sklearn, xgboost, flask, joblib
└── setup.py                              # Package: Kubernetes-Penetration-Testing-...
```

---

## 6. Kubernetes Security — Deliberate Vulnerabilities

The deployment manifests intentionally embed **8 security misconfigurations** drawn from real-world breach patterns. Each is documented with its CIS/RBAC control reference.

### Vulnerability Inventory

| # | File | Misconfiguration | Severity | CIS Control |
|---|------|-----------------|----------|-------------|
| 1 | `insecure-rbac.yaml` | ServiceAccount bound to `cluster-admin` ClusterRole | **CRITICAL** | CIS 5.1.1 |
| 2 | `k8s-deployment.yaml` | `runAsUser: 0` — container runs as root | **HIGH** | CIS 5.2.6 |
| 3 | `k8s-deployment.yaml` | `privileged: true` — full host kernel access | **CRITICAL** | CIS 5.2.1 |
| 4 | `k8s-deployment.yaml` | `allowPrivilegeEscalation: true` | **HIGH** | CIS 5.2.5 |
| 5 | `k8s-deployment.yaml` | `hostPath: /` — entire host filesystem mounted | **CRITICAL** | CIS 5.2.12 |
| 6 | `k8s-deployment.yaml` | `SECRET_PASSWORD: admin123` in env (hardcoded secret) | **HIGH** | — |
| 7 | `k8s-deployment.yaml` | Capabilities: `SYS_ADMIN`, `NET_ADMIN` added | **HIGH** | CIS 5.2.8 |
| 8 | `k8s-deployment.yaml` | `readOnlyRootFilesystem: false` | **MEDIUM** | CIS 5.2.4 |

### Vulnerability Deep-Dives

#### Vulnerability 1 — cluster-admin ServiceAccount (`insecure-rbac.yaml`)

```yaml
roleRef:
  kind: ClusterRole
  name: cluster-admin  # Grants full cluster control to the pod
```

Any process running inside the Flask pod can interact with the Kubernetes API with **unrestricted cluster-wide permissions** — read all secrets, create/delete pods in any namespace, modify RBAC rules.

**Attack scenario:** Attacker exploits a Flask vulnerability → accesses the pod → uses the mounted service account token to call `kubectl get secrets --all-namespaces`.

#### Vulnerability 3 — Privileged Container

```yaml
securityContext:
  privileged: true  # Equivalent to running as a root process on the host
```

A privileged container has full access to the host kernel — it can load kernel modules, access raw devices, and escape the container namespace entirely.

#### Vulnerability 5 — Host Root Filesystem Mount

```yaml
volumes:
  - name: host-root
    hostPath:
      path: /  # Mounts the entire host filesystem at /host inside the container
```

Combined with privileged mode and root user, this allows reading and writing any file on the Kubernetes node — including `/etc/shadow`, `/root/.ssh/`, `/var/lib/kubelet/`.

#### Vulnerability 6 — Hardcoded Secret in Environment Variable

```yaml
env:
  - name: SECRET_PASSWORD
    value: "admin123"  # Visible in kubectl describe pod, container env, /proc/$PID/environ
```

Kubernetes Secrets should be used instead — and even then, secret values should be mounted as files rather than env vars to avoid leaking via process listing.

---

## 7. kube-bench — CIS Benchmarking

kube-bench runs automated checks against the **CIS Kubernetes Benchmark** — the industry standard for K8s security configuration. This project uses CIS version 1.23.

### Running the Benchmark

```bash
# Apply the kube-bench Pod
kubectl apply -f kube-bench.yaml

# Wait for completion
kubectl wait --for=condition=completed pod/kube-bench --timeout=300s

# Retrieve JSON output
kubectl logs kube-bench > kube-bench-results.json
```

### kube-bench Pod Configuration (`kube-bench.yaml`)

```yaml
spec:
  hostPID: true                    # Access host process namespace (needed for etcd checks)
  containers:
    - name: kube-bench
      image: aquasec/kube-bench:latest
      args: ["--benchmark", "cis-1.23", "--json"]
      securityContext:
        privileged: true           # Needed to inspect host config files
      volumeMounts:
        - /var/lib/etcd            # etcd data directory
        - /etc/kubernetes          # K8s config files
        - /etc/systemd             # systemd service configs
        - /usr/bin                 # Binary inspection
        - /var/lib/kubelet         # kubelet config
```

### CIS 1.23 Check Categories

| Section | Description | Key checks |
|---------|------------|-----------|
| **1** | Control Plane Components | kube-apiserver flags, etcd encryption |
| **2** | etcd | Authentication, TLS configuration |
| **3** | Control Plane Configuration | Logging, audit policy |
| **4** | Worker Nodes | kubelet configuration, file permissions |
| **5** | Policies | RBAC, Pod Security, Network Policies, Secrets |

### Result Status Definitions

| Status | Meaning |
|--------|---------|
| **PASS** | Configuration meets the CIS requirement |
| **FAIL** | Configuration violates the CIS requirement — remediation required |
| **WARN** | Manual verification needed — tool cannot automatically determine status |
| **INFO** | Informational — no automated check available |

---

## 8. kube-hunter — Penetration Testing

kube-hunter actively probes the cluster for exploitable vulnerabilities, simulating an attacker who has already gained a foothold inside a pod.

### Running kube-hunter

```bash
# Apply the kube-hunter Job
kubectl apply -f kube-hunter.yaml

# Wait for Job completion
kubectl wait --for=condition=complete job/kube-hunter --timeout=300s

# Retrieve penetration test report
kubectl logs job/kube-hunter
```

### kube-hunter Job Configuration (`kube-hunter.yaml`)

```yaml
spec:
  containers:
    - name: kube-hunter
      image: aquasec/kube-hunter:0.6.8
      command: ["kube-hunter"]
      args: ["--pod"]              # Run from within the pod (inside-out attack)
```

The `--pod` flag simulates an attacker who has compromised a container and is now probing outward — testing what API endpoints are accessible, what metadata services are reachable, and what credentials can be extracted.

### What kube-hunter Discovers

kube-hunter tests for:
- **Kubernetes API server** exposure and anonymous access
- **etcd** direct access
- **Kubelet API** exposure (port 10250/10255)
- **Dashboard** exposure
- **Service account token** abuse potential
- **Container escape** paths
- **Sensitive information** in environment variables

Given the deliberately misconfigured deployment, kube-hunter is expected to find:

1. Service account token with cluster-admin permissions
2. Access to the Kubernetes API server from within the pod
3. Host filesystem access via the `/host` volume mount
4. Privileged container escape vectors

---

## 9. kube-bench Report Generator

`kubebench-report-generator.py` converts kube-bench's JSON output into a human-readable structured Markdown report.

### Usage

```bash
# Run after retrieving kube-bench JSON output
python kubebench-report-generator.py
# Input:  kube-bench-results.json
# Output: kube_bench_report.md
```

### Report Structure

```markdown
# Control: Master Node Security Configuration (1)
**Node Type:** master

## Section 1.1: Master Node Configuration Files
- Pass: 14
- Fail: 3
- Warn: 2
- Info: 0

### 1.1.1 - Ensure that the API server pod specification file...
- Status: PASS
- Reason: ...

### 1.1.2 - Ensure that the API server pod specification file...
- Status: FAIL
- Remediation: chmod 644 /etc/kubernetes/manifests/kube-apiserver.yaml

---

# Summary
- Total Passed:   42
- Total Failed:    8
- Total Warnings: 12
- Total Info:      3
```

### Key Implementation Details

```python
def generate_report(data, output_path="kube_bench_report.md"):
    for control in data.get("Controls", []):
        for test in control.get("tests", []):
            # Accumulate totals
            total_pass += test['pass']
            total_fail += test['fail']
            # ...
            for result in test.get("results", []):
                # Truncate long reason text at 500 chars
                lines.append(f"- Status: {result['status']}")
                if result.get('remediation'):
                    # Inline remediation commands per failed check
                    lines.append(f"- Remediation: {result['remediation']}")
```

The generator truncates `reason` fields at 500 characters and strips newlines from remediation commands to produce a clean, scannable report.

---

## 10. How to Replicate — Full Setup Guide

### Prerequisites

- Python 3.11+
- Docker
- Kubernetes cluster (minikube / kind / any K8s distribution)
- `kubectl` configured against your cluster

---

### Step 1 — Install Python Dependencies

```bash
pip install -e .
# Installs: pandas, numpy, scikit-learn, xgboost, flask, joblib, matplotlib, seaborn
```

---

### Step 2 — Train the ML Model

```bash
python pipeline/training_pipeline.py
# Generates:
#   artifacts/processed/X_train.pkl  X_test.pkl  y_train.pkl  y_test.pkl
#   artifacts/models/model.pkl
```

---

### Step 3 — Test Flask App Locally

```bash
python application.py
# http://localhost:5000 — fill in the 24 weather features → get Yes/No prediction
```

---

### Step 4 — Build and Load Docker Image

```bash
docker build -t flask-app:latest .

# For minikube:
minikube image load flask-app:latest
# For kind:
kind load docker-image flask-app:latest
```

---

### Step 5 — Deploy Vulnerable Application

```bash
kubectl create namespace vulnerable-test

# Apply RBAC (insecure — for testing only)
kubectl apply -f insecure-rbac.yaml

# Deploy the Flask app
kubectl apply -f k8s-deployment.yaml

# Verify
kubectl get pods -n vulnerable-test
kubectl get svc -n vulnerable-test
# Access: http://<node-ip>:30081
```

---

### Step 6 — Run CIS Benchmark

```bash
kubectl apply -f kube-bench.yaml
kubectl wait --for=condition=completed pod/kube-bench --timeout=300s
kubectl logs kube-bench > kube-bench-results.json

# Generate Markdown report
python kubebench-report-generator.py
cat kube_bench_report.md
```

---

### Step 7 — Run Penetration Test

```bash
kubectl apply -f kube-hunter.yaml
kubectl wait --for=condition=complete job/kube-hunter --timeout=300s
kubectl logs job/kube-hunter
```

---

### Step 8 — Clean Up

```bash
kubectl delete namespace vulnerable-test
kubectl delete pod kube-bench
kubectl delete job kube-hunter
```

---

## 11. Interpreting Security Results

### Reading kube-bench Output

Focus on **FAIL** items first — they represent concrete CIS policy violations. Common fail categories for this setup include:

| Category | Expected failures in this project |
|----------|----------------------------------|
| Pod security | Container running as root, privileged mode |
| RBAC | Excessive service account permissions |
| Secrets management | Secrets exposed in environment variables |
| Filesystem | Host path mounts, writable root filesystem |
| Capabilities | Unnecessary Linux capabilities (SYS_ADMIN, NET_ADMIN) |

### Reading kube-hunter Output

kube-hunter classifies vulnerabilities by severity:

| Severity | Meaning |
|----------|---------|
| **High** | Exploitable with immediate cluster impact |
| **Medium** | Exploitable with some conditions or lateral movement required |
| **Low** | Information disclosure or minor exposure |

### Correlating kube-bench and kube-hunter

A FAIL in kube-bench (configuration check) often corresponds to a finding in kube-hunter (exploitability check):

| kube-bench FAIL | kube-hunter finding |
|-----------------|-------------------|
| cluster-admin binding | API server access via service account token |
| `privileged: true` | Container escape / host namespace access |
| `hostPath: /` | Host filesystem read/write |
| Anonymous API access | Unauthenticated API server enumeration |

---

## 12. Remediating the Vulnerabilities

For each deliberate misconfiguration, the production-safe fix:

| Vulnerability | Fix |
|---------------|-----|
| cluster-admin RBAC | Create a minimum-privilege Role with only required verbs/resources |
| `runAsUser: 0` | Set `runAsUser: 1000` (non-root UID) |
| `privileged: true` | Remove the `privileged` field entirely (defaults to false) |
| `hostPath: /` | Remove host volume mounts; use `emptyDir` or PersistentVolumeClaims |
| Hardcoded `SECRET_PASSWORD` | Create a Kubernetes Secret: `kubectl create secret generic app-secret --from-literal=password=...` → reference via `secretKeyRef` |
| `SYS_ADMIN`, `NET_ADMIN` | Drop all capabilities: `capabilities.drop: ["ALL"]` and add only what is required |
| `allowPrivilegeEscalation: true` | Set to `false` |
| `readOnlyRootFilesystem: false` | Set to `true`; mount writable volumes only where needed |

### Production-Safe Deployment Template

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

---

## 13. How to Improve This Project

### 🔐 Security Improvements

| Area | Recommendation |
|------|---------------|
| **Add NetworkPolicy** | Restrict ingress/egress for `vulnerable-test` namespace — currently all traffic is permitted |
| **Add Pod Security Standards** | Apply `restricted` PSS via namespace label: `pod-security.kubernetes.io/enforce: restricted` |
| **Scan container image** | Run `trivy image flask-app:latest` to find OS and Python dependency CVEs |
| **Add OPA/Gatekeeper policies** | Policy-as-code to prevent privileged/root deployments at admission time |
| **Add Falco runtime detection** | Deploy Falco to detect suspicious activity in real time during the kube-hunter run |

### 🧠 ML Improvements

| Area | Recommendation |
|------|---------------|
| **Save LabelEncoders** | `application.py` expects raw integers but the form renders feature names — save all encoders and add a preprocessing layer at inference |
| **Handle class imbalance** | Add `scale_pos_weight` to XGBoost or use SMOTE — 77:23 split means minority class (Rain=Yes) has lower recall |
| **Hyperparameter tuning** | Default XGBoost is 89.7% train / 86.6% test — add GridSearchCV for `max_depth`, `learning_rate`, `n_estimators` |
| **Add MLflow tracking** | Log accuracy, precision, recall, F1, and model artifacts per run |

---

## 14. Troubleshooting

| Error / Symptom | Fix |
|----------------|-----|
| `model.pkl not found` | Run `python pipeline/training_pipeline.py` first |
| Pod stuck in `Pending` | Check node resources; for minikube run `minikube start --memory=4096` |
| `ImagePullBackOff` | Image not available in cluster — run `minikube image load flask-app:latest` |
| kube-bench Pod stays `Running` | Increase `--timeout` in kubectl wait; benchmark can take 2–5 minutes |
| kube-bench reports no `Controls` | JSON output may be empty — check `kubectl logs kube-bench --previous` |
| `kubebench-report-generator.py` KeyError | kube-bench JSON schema differs by K8s version — update key paths to match your output |
| kube-hunter Job completes instantly with no output | Check for `--pod` flag in the Job spec; ensure the pod had network access |

---

## 15. Glossary

| Term | Definition |
|------|-----------|
| **kube-bench** | Aqua Security tool that checks Kubernetes configuration against the CIS Kubernetes Benchmark |
| **kube-hunter** | Aqua Security tool that actively probes a Kubernetes cluster for exploitable vulnerabilities |
| **CIS Benchmark** | Center for Internet Security's prescriptive security configuration guidelines — CIS-1.23 covers Kubernetes 1.23 |
| **RBAC** | Role-Based Access Control — Kubernetes mechanism for controlling who can do what to which resources |
| **cluster-admin** | Built-in Kubernetes ClusterRole granting unrestricted access to all cluster resources |
| **ClusterRoleBinding** | Binds a ClusterRole to subjects (ServiceAccounts, users) cluster-wide |
| **ServiceAccount** | Kubernetes identity for processes running in pods |
| **Privileged container** | Container with full access to the host kernel — equivalent to running as root on the node |
| **hostPath** | Kubernetes volume type that mounts a host filesystem path directly into the container |
| **SYS_ADMIN** | Linux capability granting privileged system operations — mount filesystems, modify kernel parameters |
| **NET_ADMIN** | Linux capability granting network interface configuration — can intercept traffic |
| **Pod Security Standards (PSS)** | Kubernetes built-in policies: `privileged`, `baseline`, `restricted` |
| **OPA/Gatekeeper** | Open Policy Agent — policy-as-code engine for Kubernetes admission control |
| **Falco** | Cloud-native runtime security tool for detecting suspicious behaviour in containers |
| **RainTomorrow** | Target variable — binary: `No` (0) or `Yes` (1) |
| **LabelEncoder** | Scikit-learn encoder converting string categories to integer indices |
| **mean imputation** | Filling missing numerical values with the column mean |
| **hostPID** | Pod spec option allowing the container to share the host's process namespace |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Tanmoy Saha**
[linkedin.com/in/sahatanmoyofficial](https://linkedin.com/in/sahatanmoyofficial) | sahatanmoyofficial@gmail.com

