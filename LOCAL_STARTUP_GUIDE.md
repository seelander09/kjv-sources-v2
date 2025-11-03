# KJV Sources - Local Startup Guide

## 🚀 Quick Start (Recommended)

The easiest way to start your local KJV Sources system:

```powershell
# Start everything with one command
.\start_local_system.ps1

# Stop everything when done
.\stop_local_system.ps1
```

## 📋 What Gets Started

The startup script automatically handles:

1. **Docker Desktop** - Starts if not running
2. **Weaviate Vector Database** - Your migrated data storage
3. **Elysia API Server** - The main application interface
4. **Health Checks** - Ensures everything is working
5. **Status Monitoring** - Shows you what's running

## 🔧 Alternative Startup Methods

### Method 1: Docker Compose (Containerized)

```powershell
# Start just Weaviate
.\start_docker_compose.ps1 -Profile weaviate

# Start Weaviate + API
.\start_docker_compose.ps1 -Profile api

# Start everything (production-like)
.\start_docker_compose.ps1 -Profile production
```

### Method 2: Manual Step-by-Step

```powershell
# 1. Start Docker Desktop (if not running)
# 2. Start Weaviate
.\start_weaviate.ps1

# 3. Start API
.\start_elysia.ps1
```

## 🌐 Access Your System

Once started, you can access:

- **Main Interface**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Weaviate Console**: http://localhost:8080/v1/meta
- **System Status**: `python system_status_summary.py`

## 🛠️ Troubleshooting

### Common Issues

**Docker Desktop not starting:**
```powershell
# Start Docker Desktop manually, then retry
.\start_local_system.ps1 -SkipDocker
```

**Weaviate connection issues:**
```powershell
# Force restart Weaviate container
.\start_local_system.ps1 -ForceRestart
```

**API server won't start:**
```powershell
# Check if port 8001 is in use
netstat -ano | findstr :8001

# Kill any processes using the port
.\stop_local_system.ps1 -Force
```

### Health Checks

```powershell
# Check system status
python system_status_summary.py

# Check specific services
curl http://localhost:8080/v1/meta  # Weaviate
curl http://localhost:8001/api/elysia/status  # API
```

### Logs and Debugging

```powershell
# Start with logs
.\start_local_system.ps1 -ShowLogs

# View Docker logs
docker logs kjv-weaviate

# View API logs
Get-Content elysia_integration.log -Tail 20
```

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Docker        │    │   Weaviate      │    │   Elysia API    │
│   Desktop       │───▶│   Vector DB     │◀───│   Server        │
│                 │    │   (Port 8080)   │    │   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Your Data     │
                       │   (Migrated)    │
                       └─────────────────┘
```

## 🔄 Data Flow

1. **Weaviate** stores your migrated KJV Sources data
2. **Elysia API** provides intelligent query processing
3. **Docker** manages the Weaviate container
4. **No API keys required** for local development

## 🎯 Usage Examples

### Start and Test

```powershell
# Start the system
.\start_local_system.ps1

# Test with a query
curl -X POST http://localhost:8001/api/elysia/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find verses about creation in Genesis"}'

# Check status
python system_status_summary.py
```

### Development Workflow

```powershell
# Start development environment
.\start_local_system.ps1

# Make changes to your code
# (API auto-reloads with changes)

# Test changes
curl http://localhost:8001/api/elysia/status

# Stop when done
.\stop_local_system.ps1
```

## 🔧 Configuration

### Environment Variables

The system uses these configurations:

- **Weaviate**: `http://localhost:8080` (no auth required)
- **API Port**: `8001`
- **Docker Container**: `kjv-weaviate`
- **Data Volume**: `weaviate_data`

### Customization

Edit these files to customize:

- `elysia_config_local.json` - API and database settings
- `docker-compose.yml` - Container configuration
- `start_local_system.ps1` - Startup behavior

## 📝 Script Parameters

### start_local_system.ps1

```powershell
-SkipDocker      # Don't start Docker Desktop
-SkipWeaviate    # Don't start Weaviate
-SkipAPI         # Don't start API server
-ForceRestart    # Force restart containers
-ShowLogs        # Show logs after startup
```

### stop_local_system.ps1

```powershell
-StopDocker      # Also stop Docker Desktop
-Force           # Force kill processes
-ShowLogs        # Show logs before stopping
```

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: `.\start_local_system.ps1 -ShowLogs`
2. **Verify Docker**: `docker info`
3. **Check ports**: `netstat -ano | findstr :8080`
4. **Restart clean**: `.\stop_local_system.ps1 -Force` then `.\start_local_system.ps1`

## 🎉 Success Indicators

You'll know everything is working when you see:

```
✅ Docker Desktop is running
✅ Weaviate is ready at: http://localhost:8080
✅ Elysia API is ready at: http://localhost:8001
🎉 Local system startup completed!
```

Then you can open http://localhost:8001 in your browser and start asking questions about your biblical data!
