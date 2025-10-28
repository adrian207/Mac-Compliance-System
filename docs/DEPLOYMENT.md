# Deployment Guide

**Author:** Adrian Johnson <adrian207@gmail.com>

## Deployment Overview

This guide covers deploying the Mac OS Zero Trust Endpoint Security Platform in various environments.

---

## Prerequisites

**System Requirements**
- Python 3.10 or higher
- PostgreSQL 13 or higher
- Redis 6 or higher
- 4GB RAM minimum (8GB recommended)
- 50GB disk space minimum

**Required Credentials**
- Kandji API token and tenant ID
- Zscaler API credentials
- Seraphic API key
- SMTP credentials (for email alerts)

---

## Local Development Deployment

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd Mac-Hardening

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings

# Initialize database
python scripts/init_database.py

# Run setup
python scripts/setup.py

# Start platform
python main.py
```

### Running API Server

In a separate terminal:

```bash
source venv/bin/activate
python api_server.py
```

Access the API documentation at: `http://localhost:8000/docs`

---

## Docker Deployment

### Using Docker Compose (Recommended)

**Step 1: Configure Environment**

Create `.env` file:

```bash
DB_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
```

**Step 2: Configure Application**

```bash
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings
```

**Step 3: Deploy**

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f platform

# Check status
docker-compose ps
```

**Step 4: Initialize Database**

```bash
docker-compose exec platform python scripts/init_database.py
```

### Manual Docker Build

```bash
# Build image
docker build -t zerotrust-platform:latest .

# Run PostgreSQL
docker run -d \
  --name zerotrust-db \
  -e POSTGRES_DB=zerotrust_security \
  -e POSTGRES_USER=zerotrust_user \
  -e POSTGRES_PASSWORD=changeme \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15

# Run Redis
docker run -d \
  --name zerotrust-redis \
  --restart unless-stopped \
  redis:7-alpine

# Run Platform
docker run -d \
  --name zerotrust-platform \
  --link zerotrust-db:postgres \
  --link zerotrust-redis:redis \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -p 8000:8000 \
  -p 9090:9090 \
  zerotrust-platform:latest
```

---

## Cloud Deployment

### AWS Deployment

**Architecture:**
- EC2 instances for application servers
- RDS PostgreSQL for database
- ElastiCache Redis for caching
- Application Load Balancer for high availability
- CloudWatch for monitoring

**Deployment Steps:**

1. **Create RDS PostgreSQL Instance**

```bash
aws rds create-db-instance \
  --db-instance-identifier zerotrust-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username zerotrust_user \
  --master-user-password <password> \
  --allocated-storage 100 \
  --vpc-security-group-ids sg-xxxxx
```

2. **Create ElastiCache Redis**

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id zerotrust-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1
```

3. **Launch EC2 Instances**

Use provided CloudFormation template or:

```bash
# Create EC2 instance
aws ec2 run-instances \
  --image-id ami-xxxxx \
  --instance-type t3.large \
  --key-name your-key \
  --security-group-ids sg-xxxxx \
  --user-data file://deploy/user-data.sh
```

4. **Configure Application**

```bash
ssh ec2-user@<instance-ip>
cd /opt/zerotrust-platform
# Edit config/config.yaml
python scripts/init_database.py
sudo systemctl start zerotrust-platform
```

### Azure Deployment

**Architecture:**
- Azure Virtual Machines for application
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Load Balancer
- Azure Monitor

**Deployment Steps:**

1. **Create Resource Group**

```bash
az group create \
  --name zerotrust-rg \
  --location eastus
```

2. **Create PostgreSQL Database**

```bash
az postgres server create \
  --resource-group zerotrust-rg \
  --name zerotrust-db \
  --location eastus \
  --admin-user zerotrust_user \
  --admin-password <password> \
  --sku-name B_Gen5_2
```

3. **Create Redis Cache**

```bash
az redis create \
  --resource-group zerotrust-rg \
  --name zerotrust-redis \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

4. **Deploy Application**

```bash
# Create VM
az vm create \
  --resource-group zerotrust-rg \
  --name zerotrust-vm \
  --image UbuntuLTS \
  --size Standard_D2s_v3 \
  --admin-username azureuser \
  --ssh-key-values @~/.ssh/id_rsa.pub

# Configure and deploy application
```

### Google Cloud Platform Deployment

**Architecture:**
- Compute Engine instances
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Load Balancing
- Cloud Monitoring

**Deployment Steps:**

1. **Create Cloud SQL Instance**

```bash
gcloud sql instances create zerotrust-db \
  --database-version=POSTGRES_14 \
  --cpu=2 \
  --memory=8GB \
  --region=us-central1
```

2. **Create Redis Instance**

```bash
gcloud redis instances create zerotrust-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_6_x
```

3. **Deploy to Compute Engine**

```bash
gcloud compute instances create zerotrust-vm \
  --machine-type=n1-standard-2 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --metadata-from-file startup-script=deploy/startup.sh
```

---

## Kubernetes Deployment

### Using Helm Chart

```bash
# Add Helm repository
helm repo add zerotrust https://charts.example.com/zerotrust

# Install chart
helm install zerotrust zerotrust/zerotrust-platform \
  --set database.host=postgres-service \
  --set redis.host=redis-service \
  --set config.kandji.apiToken=<token>
```

### Manual Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/secrets.yaml
kubectl apply -f deploy/k8s/postgresql.yaml
kubectl apply -f deploy/k8s/redis.yaml
kubectl apply -f deploy/k8s/platform.yaml
kubectl apply -f deploy/k8s/service.yaml
kubectl apply -f deploy/k8s/ingress.yaml

# Check status
kubectl get pods -n zerotrust
```

---

## Production Configuration

### High Availability Setup

**Database Replication:**

```yaml
database:
  primary:
    host: db-primary.example.com
  replicas:
    - host: db-replica-1.example.com
    - host: db-replica-2.example.com
  connection_pool:
    min_size: 10
    max_size: 50
```

**Load Balancing:**

Configure load balancer to distribute traffic across multiple API server instances:

```nginx
upstream zerotrust_api {
    server api-1.example.com:8000;
    server api-2.example.com:8000;
    server api-3.example.com:8000;
}

server {
    listen 443 ssl;
    server_name api.zerotrust.example.com;
    
    location / {
        proxy_pass http://zerotrust_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Security Hardening

**SSL/TLS Configuration:**

```yaml
api:
  ssl:
    enabled: true
    certificate: /path/to/cert.pem
    key: /path/to/key.pem
    min_tls_version: "1.3"
```

**API Key Authentication:**

```yaml
api:
  authentication:
    enabled: true
    api_keys:
      - name: "Service A"
        key: "encrypted_key_here"
        permissions: ["read", "write"]
```

**Network Security:**

- Use VPC/VNET isolation
- Configure security groups/firewall rules
- Enable encryption in transit and at rest
- Use private subnets for databases
- Implement network segmentation

### Monitoring and Observability

**Prometheus Configuration:**

```yaml
monitoring:
  prometheus:
    enabled: true
    port: 9090
    scrape_interval: 15s
    retention_days: 30
```

**Grafana Dashboards:**

Import pre-built dashboards from `deploy/grafana/`

**Log Aggregation:**

Configure centralized logging:

```yaml
logging:
  aggregation:
    enabled: true
    backend: "elasticsearch"
    endpoint: "https://logs.example.com:9200"
    index_prefix: "zerotrust"
```

---

## Backup and Recovery

### Database Backups

**Automated Backups:**

```bash
# Daily backup script
#!/bin/bash
pg_dump -h $DB_HOST -U $DB_USER -d zerotrust_security \
  | gzip > /backups/zerotrust-$(date +%Y%m%d).sql.gz

# Retain last 30 days
find /backups -name "zerotrust-*.sql.gz" -mtime +30 -delete
```

**Restore from Backup:**

```bash
gunzip < /backups/zerotrust-20250128.sql.gz \
  | psql -h $DB_HOST -U $DB_USER -d zerotrust_security
```

### Disaster Recovery

**Recovery Time Objective (RTO):** 4 hours  
**Recovery Point Objective (RPO):** 1 hour

**DR Procedures:**

1. Restore database from latest backup
2. Deploy application to standby infrastructure
3. Update DNS to point to DR environment
4. Verify all integrations are functional
5. Resume normal operations

---

## Scaling

### Horizontal Scaling

**API Servers:**

Deploy multiple API server instances behind load balancer:

```bash
# Scale up
for i in {1..5}; do
  docker-compose up -d --scale api=$i
done
```

**Database Read Replicas:**

Configure read replicas for improved query performance:

```python
# In config.yaml
database:
  read_replicas:
    - host: replica1.db.example.com
    - host: replica2.db.example.com
```

### Vertical Scaling

Increase resources for existing instances:

- Upgrade instance types
- Increase database storage
- Add more memory for caching

---

## Troubleshooting

### Common Issues

**Database Connection Failures:**

```bash
# Check database connectivity
psql -h $DB_HOST -U $DB_USER -d zerotrust_security

# Verify connection pooling
python -c "from core.database import get_db_manager; get_db_manager()"
```

**Integration Errors:**

```bash
# Test integrations
python scripts/test_integrations.py

# Check API credentials
python -c "from integrations.kandji import get_kandji_client; \
           get_kandji_client().test_connection()"
```

**Performance Issues:**

```bash
# Check database performance
psql -c "SELECT * FROM pg_stat_activity;"

# Monitor resource usage
docker stats zerotrust-platform

# Review slow queries
tail -f logs/platform.log | grep "slow_query"
```

---

## Maintenance

### Updating the Platform

```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run database migrations
python scripts/migrate_database.py

# Restart services
docker-compose restart platform api
```

### Database Maintenance

```bash
# Vacuum database
psql -c "VACUUM ANALYZE;"

# Reindex
psql -c "REINDEX DATABASE zerotrust_security;"

# Update statistics
psql -c "ANALYZE;"
```

---

## Support

For deployment assistance, contact:  
**Adrian Johnson** <adrian207@gmail.com>

