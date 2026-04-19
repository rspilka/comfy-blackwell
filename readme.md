# ComfyUI Docker (Blackwell Optimized)

This repository provides a modular, multi-stage Docker environment specifically tuned for **NVIDIA Blackwell GPUs (RTX 50-series)**. The architecture follows the "Build Distillation" principle, strictly separating the heavy compilation environment from the lean production runtime to ensure zero-bloat and maximum performance.

## Index
1. [Image Overview & Docker Hub](#1-image-overview--docker-hub)
2. [Project Purpose & Image Contents](#2-project-purpose--image-contents)
3. [Multi-Stage Build Architecture (The Distillation)](#3-multi-stage-build-architecture-the-distillation)
4. [Dockerfile Parameterization (Build Args)](#4-dockerfile-parameterization-build-args)
5. [Docker Compose Architecture](#5-docker-compose-architecture)
6. [Service Roles & Interaction](#6-service-roles--interaction)
7. [Hardware/Software Requirements & Build Recommendations](#7-hardwaresoftware-requirements--build-recommendations)

---

## 1. Image Overview & Docker Hub

Images are optimized for different deployment scenarios and are available on Docker Hub:

| Image Tag | Docker Hub Link | Description |
| :--- | :--- | :--- |
| `latest` | [rspilka/comfy:latest](https://hub.docker.com/r/rspilka/comfy) | Production-ready slim build. |
| `comfy-blackwell-heavy` | [rspilka/comfy:heavy](https://hub.docker.com/r/rspilka/comfy) | Full-featured build including pre-loaded custom nodes. |
| `stage-base` | [rspilka/comfy:base](https://hub.docker.com/r/rspilka/comfy) | Basic environment for custom layer stacking. |

---

## 2. Project Purpose & Image Contents

### Purpose
* **Blackwell Optimization:** Engineered to leverage FP8 precision and Triton kernels for maximum throughput on RTX 50-series hardware.
* **Zero-Bloat Strategy:** Eliminates compilers, headers, and git history from the final execution layer.
* **Permissions Harmony:** Implements dynamic UID/GID mapping for host user file ownership.

### Image Contents & Stage Differentiation
Each stage serves a distinct purpose to optimize the final image size and build reliability:
* **Base Stage:** Foundational layer with NVIDIA PyTorch core and "Chameleon" user logic.
* **Extended Stage:** Builder environment with `build-essential`, `ninja`, and `python3-dev`.
* **Heavy Build Stage:** Assembler for cloning and installing requirements for all custom nodes.

---

## 3. Multi-Stage Build Architecture (The Distillation)

The build isolates the **Build Environment** from the **Runtime Image** through 5 phases:

1. **Stage 1: `base`**: Fundamental setup and identity.
2. **Stage 2: `extended`**: Deployment of compilation tools.
3. **Stage 3: `heavy`**: Repository cloning and extension compilation.
4. **Stage 4: `pre-flight` (Stage Aliasing)**: This is a logical "Switch" stage. It uses the `BUILD_TARGET` argument to rename (alias) either the `base` or `heavy` stage to `pre-flight`. This ensures the final stage remains agnostic of the build complexity..
5. **Stage 5: `final`**: Distilled runtime containing only site-packages and app files.

---

## 4. Dockerfile Parameterization (Build Args)

| Parameter | Default | Purpose |
| :--- | :--- | :--- |
| `BASE_IMAGE` | `nvcr.io/nvidia/pytorch:26.03-py3` | Swappable NVIDIA foundation. |
| `USERNAME` | `comfy` | Internal container username. |
| `USER_UID` | `1000` | Target UID to match host user. |
| `USER_GID` | `1000` | Target GID to match host group. |
| `TORCH_CUDA_ARCH_LIST` | `10.0` | Target architecture (10.0 for Blackwell). |

**Build Example:**
```bash
docker build --target final \
  --build-arg BASE_IMAGE="nvcr.io/nvidia/pytorch:26.03-py3" \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t comfy-blackwell-heavy:latest .
```

---

## 5. Docker Compose Architecture

Orchestration of 8 containers for inference, monitoring, and status tracking.

* **`comfy-worker-heavy`**: Core backend engine.
* **`comfy-monitor`**: Real-time status hub for job queues.
* **`comfy-gallery`**: Image browser for `./output`.
* **`prometheus` / `gpu-exporter` / `node-exporter` / `grafana` / `pushgateway`**: Monitoring stack.

---

## 6. Service Roles & Interaction

Services communicate via the **`comfy-net`** bridge:
1. **Inference & Jobs:** The `comfy-monitor` interacts with `comfy-worker-heavy` to provide real-time updates.
2. **Metrics Loop:** Prometheus scrapes hardware data from exporters and software status from the monitor.
3. **Visualization:** Grafana correlates generation tasks with hardware load.

---

## 7. Hardware/Software Requirements & Build Recommendations

### Hardware Requirements
* **GPU:** NVIDIA Blackwell (RTX 50-series). Minimum 12GB VRAM.
* **RAM:** Minimum 32GB (64GB recommended).
* **Disk:** 100GB+ free space.

---
