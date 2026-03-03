# High-Performance Blog Microservices Architecture

An event-driven, highly scalable microservices architecture designed for a blogging platform. Built with **FastAPI**, *
*Apache Kafka**, **PostgreSQL**, and **Redis**, and fully orchestrated using **Kubernetes**.

This project demonstrates how to handle high-throughput read/write operations by decoupling services, implementing the
Cache-Aside pattern, and utilizing asynchronous message brokering to prevent database bottlenecks.

## 🏗 Architecture Overview

The system consists of an NGINX Ingress API Gateway that routes traffic to four independent microservices. Background
tasks and cross-service communication are handled asynchronously via Apache Kafka.

* **API Gateway (NGINX Ingress):** Single entry point (`api.blog.local`) routing requests to appropriate backend
  services.
* **Auth Service:** Handles user registration, authentication, and JWT generation.
* **Post Service:** Manages blog post creation and retrieval. Utilizes Redis for sub-millisecond read operations and
  publishes events to Kafka on post creation/reads.
* **View Service:** An independent consumer that listens to Kafka events to increment post view counts asynchronously,
  protecting the main database from read/write locks.
* **Notification Service:** Consumes Kafka events to generate system notifications when a new post is published.

### Tech Stack

* **Framework:** FastAPI (Python 3.10+)
* **Message Broker:** Apache Kafka & Zookeeper (AIOKafka)
* **Databases:** PostgreSQL (4 isolated instances for each service)
* **Caching:** Redis (Cache-Aside pattern)
* **Authentication:** JWT (JSON Web Tokens) with HTTPBearer
* **Infrastructure:** Docker, Docker Compose, Kubernetes (Manifests, ConfigMaps, Secrets, Ingress)
* **Load Testing:** Locust

## 🚀 Performance & Load Testing Results

The architecture is specifically optimized to prevent the classic `QueuePool limit overflow` in PostgreSQL by offloading
read-heavy requests to Redis and write-heavy background tasks to Kafka.

**Locust Load Test Benchmark:**

* **Concurrent Users:** 1,000
* **Spawn Rate:** 20 users/second
* **Total Requests Handled:** 17,114+
* **Requests Per Second (RPS):** ~495.3
* **Failure Rate:** **0%**
* **Average Response Time:** **15.43 ms**
* **95th Percentile:** 57 ms

*Database connections remain stable under heavy load, with Redis serving the majority of `GET` requests directly from
RAM.*

## ⚙️ Local Setup & Deployment

### Prerequisites

* Docker & Docker Desktop (or Minikube)
* Kubernetes enabled
* `kubectl` CLI tool

### 1. Build Docker Images

Run the following commands in the root directory to build local images for Kubernetes:

```bash
docker build -t auth_service:latest ./auth_service
docker build -t post_service:latest ./post_service
docker build -t view_service:latest ./view_service
docker build -t notification_service:latest ./notification_service
```

### 2. Configure Local DNS (Hosts File)

Map the API Gateway domain to your local loopback address.

* Mac/Linux: Add 127.0.0.1 api.blog.local to /etc/hosts
* Windows: Add 127.0.0.1 api.blog.local to C:\Windows\System32\drivers\etc\hosts

### 3. Deploy to Kubernetes

* Apply the Kubernetes manifests to spin up the entire cluster (ConfigMaps, Secrets, Databases, Kafka, Redis, and APIs):

```bash
kubectl apply -f k8s/
```

* Check the status of your pods to ensure everything is running:

```bash
kubectl get pods -w
```

## Authentication Flow

*
    1. Obtain a JWT by sending a POST request to http://api.blog.local/auth/login.
*
    2. Attach the token as a Bearer Token in the Authorization header for protected routes (e.g., creating a post via
       the Post Service).

## 📄 License
* This project is open-source and available under the MIT License.