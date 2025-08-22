# Complete Documentation for doobidoo/mcp-memory-service

The doobidoo/mcp-memory-service is a universal Model Context Protocol (MCP) server providing semantic memory search, persistent storage, and autonomous memory consolidation for AI assistants. **Version 6.2.0** introduces native Cloudflare backend integration for global edge distribution, while **version 5.0.0** established SQLite-vec as the default backend, delivering 10x faster startup and 75% reduced memory usage compared to previous versions. The service integrates seamlessly with 13+ AI applications including Claude Desktop, VS Code, Cursor, Continue, WindSurf, LM Studio, and Zed.

## Full installation instructions for all platforms

### Docker deployment offers the fastest path to production

The service provides two Docker images optimized for different deployment scenarios. The standard image includes PyTorch and CUDA support for maximum performance, while the slim variant uses ONNX Runtime for CPU-only deployments, reducing the image size from 3GB to approximately 300MB.

```bash
# Standard image with PyTorch + CUDA support
docker pull doobidoo/mcp-memory-service:latest
docker run -d -p 8000:8000 \
  -v $(pwd)/data/sqlite_db:/app/sqlite_db \
  -v $(pwd)/data/backups:/app/backups \
  doobidoo/mcp-memory-service:latest

# Slim image for CPU-only environments
docker pull doobidoo/mcp-memory-service:slim
docker run -d -p 8000:8000 \
  -v $(pwd)/data/sqlite_db:/app/sqlite_db \
  -v $(pwd)/data/backups:/app/backups \
  doobidoo/mcp-memory-service:slim
```

For development and testing scenarios, standalone mode prevents boot loops and enables direct HTTP API access:

```bash
docker run -d -p 8000:8000 \
  -e MCP_STANDALONE_MODE=1 \
  -v $(pwd)/data/sqlite_db:/app/sqlite_db \
  -v $(pwd)/data/backups:/app/backups \
  doobidoo/mcp-memory-service:latest
```

### Python installation with intelligent hardware detection

The intelligent installer automatically detects your hardware configuration and recommends optimal settings. This approach ensures compatibility across diverse platforms while maximizing performance based on available resources.

```bash
git clone https://github.com/doobidoo/mcp-memory-service.git
cd mcp-memory-service

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run intelligent installer with hardware detection
python install.py
```

The installer supports numerous configuration options for specific deployment scenarios:

```bash
# Storage backend selection
python install.py --storage-backend sqlite_vec    # Default, recommended
python install.py --storage-backend chromadb      # Legacy, deprecated

# Platform-specific optimizations
python install.py --legacy-hardware               # 2013-2017 Intel Macs
python install.py --server-mode                   # Headless deployment
python install.py --enable-http-api              # HTTP/SSE API development

# Multi-client and Claude Code integration
python install.py --setup-multi-client           # Configure all clients
python install.py --install-claude-commands      # Install CC commands
```

### Platform-specific installation requirements

**Windows** requires special PyTorch handling due to platform-specific wheel availability. The Windows installation script automatically detects CUDA availability and installs the appropriate PyTorch version:

```bash
python scripts/install_windows.py

# Manual installation if needed
pip install torch==2.1.0 torchvision==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt --no-deps
pip install "mcp>=1.0.0,<2.0.0"
pip install -e .
```

**macOS Intel** processors face known dependency conflicts between PyTorch and sentence-transformers. The installer handles these automatically, but manual resolution may be required:

```bash
# Force compatible dependencies
python install.py --force-compatible-deps

# Manual fix for Intel Macs
pip uninstall -y torch torchvision torchaudio sentence-transformers
pip install torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1
pip install sentence-transformers==2.2.2
pip install chromadb==0.5.23 tokenizers==0.20.3 mcp>=1.0.0,<2.0.0
```

**Apple Silicon** Macs benefit from Metal Performance Shaders (MPS) acceleration:

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
python install.py
```

### Quick installation methods for rapid deployment

Claude Desktop users can leverage the Smithery auto-installer for one-click setup:

```bash
npx -y @smithery/cli install @doobidoo/mcp-memory-service --client claude
```

The uvx tool provides isolated execution without environment contamination:

```bash
# Install uv package manager
pip install uv
# or
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run memory service directly
uvx mcp-memory-service

# Install from GitHub
uvx --from git+https://github.com/doobidoo/mcp-memory-service.git mcp-memory-service
```

## Complete configuration options and environment variables

### Core storage configuration defines backend behavior

The service supports three distinct storage backends, each optimized for specific use cases. SQLite-vec serves as the default since version 5.0.0, offering superior performance for most deployments.

```bash
# Storage backend selection
MCP_MEMORY_STORAGE_BACKEND=sqlite_vec    # Default, fast, lightweight
MCP_MEMORY_STORAGE_BACKEND=chromadb      # Legacy, deprecated
MCP_MEMORY_STORAGE_BACKEND=cloudflare    # Global edge distribution

# SQLite-vec configuration
MCP_MEMORY_SQLITE_PATH=/path/to/sqlite_vec.db

# ChromaDB configuration (deprecated)
MCP_MEMORY_CHROMA_PATH=/path/to/chroma_db

# Backup configuration
MCP_MEMORY_BACKUPS_PATH=/path/to/backups
AUTO_BACKUP_INTERVAL=24                    # Hours between backups
BACKUP_RETENTION_DAYS=7                    # Days to retain backups
```

### Performance tuning parameters optimize resource usage

These settings control memory usage, query performance, and system behavior based on available resources:

```bash
# Query and retrieval settings
MAX_RESULTS_PER_QUERY=10                   # Maximum results per search
SIMILARITY_THRESHOLD=0.7                   # Semantic similarity threshold
MCP_MEMORY_BATCH_SIZE=16                   # Processing batch size

# Database optimization
MAX_MEMORIES_BEFORE_OPTIMIZE=10000         # Trigger optimization threshold

# Hardware acceleration
PYTORCH_ENABLE_MPS_FALLBACK=1             # Apple Silicon MPS
MCP_MEMORY_USE_ONNX=1                     # CPU-only ONNX runtime
MCP_MEMORY_USE_DIRECTML=1                 # Windows DirectML
MCP_MEMORY_USE_ROCM=1                     # AMD ROCm support

# Operational modes
MCP_STANDALONE_MODE=1                      # Enable standalone HTTP mode
LOG_LEVEL=INFO                            # Logging verbosity
```

### Memory consolidation system configuration

The revolutionary dream-inspired consolidation system automatically organizes and compresses memories over time:

```bash
# Enable autonomous consolidation
MCP_CONSOLIDATION_ENABLED=true
MCP_CONSOLIDATION_ARCHIVE_PATH=/path/to/archive

# Retention periods (days)
MCP_RETENTION_CRITICAL=365                # Critical memories
MCP_RETENTION_REFERENCE=180               # Reference materials
MCP_RETENTION_STANDARD=30                 # Standard memories
MCP_RETENTION_TEMPORARY=7                 # Temporary memories

# Association discovery
MCP_ASSOCIATION_MIN_SIMILARITY=0.3        # Minimum similarity for connections
MCP_ASSOCIATION_MAX_SIMILARITY=0.7        # Maximum similarity threshold

# Scheduling (cron-style)
MCP_SCHEDULE_DAILY="02:00"                # Daily at 2 AM
MCP_SCHEDULE_WEEKLY="SUN 03:00"           # Sundays at 3 AM
MCP_SCHEDULE_MONTHLY="01 04:00"           # 1st of month at 4 AM
```

### Cloudflare backend enables global edge distribution

Version 6.2.0 introduces native Cloudflare integration for serverless scaling and worldwide low-latency access:

```bash
MCP_MEMORY_STORAGE_BACKEND=cloudflare
CLOUDFLARE_API_TOKEN=your-api-token
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_VECTORIZE_INDEX=mcp-memory-index
CLOUDFLARE_D1_DATABASE_ID=your-d1-database-id
CLOUDFLARE_R2_BUCKET=mcp-memory-content      # Optional for large content
```

## All available MCP tools and functions

### Core memory operations handle storage and retrieval

**store_memory** creates new memories with optional categorization and metadata. The tool accepts content strings up to 10,000 characters and supports unlimited tags for flexible organization:

```javascript
{
  "content": "Project deadline is May 15th",
  "tags": ["work", "deadlines", "important"],
  "metadata": {
    "type": "deadline",
    "priority": "high",
    "project": "Q2 Launch"
  }
}
```

**retrieve_memory** performs semantic search across stored memories, utilizing vector similarity to find conceptually related content even when exact terms don't match:

```javascript
{
  "query": "database architecture decisions",
  "similarity_threshold": 0.7,    // Minimum similarity score (0-1)
  "max_results": 10,              // Result limit
  "tags": ["architecture"]        // Optional tag filter
}
```

**recall_memory** interprets natural language time expressions to retrieve temporally relevant memories:

```javascript
{
  "time_expression": "what did we decide last week?",
  "max_results": 5
}
```

### Memory management tools provide maintenance capabilities

**delete_memory** removes specific memories by their unique hash identifier, while **delete_by_tag** offers flexible deletion with both OR and AND logic for multi-tag operations. The enhanced **delete_by_all_tags** function requires all specified tags to be present, enabling precise cleanup of memories matching complex criteria.

**cleanup_duplicates** identifies and removes duplicate entries automatically, using content hashing and similarity detection to maintain database integrity. **optimize_db** reorganizes the database for improved performance, particularly beneficial after bulk operations or when approaching the optimization threshold.

### Database operations ensure system reliability

**create_backup** generates timestamped backups in tar.gz format, preserving the complete memory state including all metadata and associations:

```javascript
{
  "backup_path": "/custom/backup/location",  // Optional
  "compression": "gzip"                      // Default compression
}
```

**get_stats** provides comprehensive database metrics including total memory count, unique tags, storage usage, and performance indicators. **check_database_health** returns a health score from 0-100% along with detailed diagnostics about query performance, storage efficiency, and potential issues.

### Consolidation system tools manage autonomous organization

**consolidate_memories** manually triggers consolidation for specific time horizons (daily, weekly, monthly, quarterly, yearly), while **get_consolidation_health** monitors system status and processing queue depth. **get_memory_associations** explores discovered connections between memories, revealing non-obvious relationships identified by the consolidation algorithm.

**schedule_consolidation** configures autonomous processing schedules using cron-style syntax, and **get_consolidation_recommendations** provides AI-powered suggestions for memory organization and cleanup based on usage patterns.

### Claude Code commands enable conversational interaction

Version 2.2.0 introduced direct commands for Claude Desktop users:

- `/memory-store "content" [--tags tag1,tag2]` - Store with automatic context detection
- `/memory-recall "time expression or query"` - Natural language retrieval
- `/memory-search [--tags tag1,tag2] [--query "terms"]` - Advanced filtering
- `/memory-context [--summary "description"]` - Capture session context
- `/memory-health` - System status and statistics

## Storage backend architecture and capabilities

### SQLite-vec delivers optimal performance for most deployments

Built on Alex Garcia's sqlite-vec extension, this backend provides native vector search within SQLite using SIMD-accelerated operations. The architecture employs chunked storage to reduce memory fragmentation while maintaining excellent query performance through AVX (x86) and NEON (ARM) intrinsics.

**Performance characteristics** demonstrate significant advantages over alternatives. Startup completes in 2-3 seconds compared to ChromaDB's 15-30 seconds, while memory usage remains below 50MB for 1,000 memories versus ChromaDB's 200MB requirement. Query operations typically complete in under 100ms with proper indexing, and the single-file database format simplifies backup and migration procedures.

The backend supports both JSON and compact binary formats for vector storage, with configurable dimensions (typically 384-768 for sentence transformers) and multiple distance metrics including L2, cosine similarity, and L1 distances. Optional int8 quantization further reduces storage requirements without significant accuracy loss.

### ChromaDB provides legacy compatibility

Although deprecated and scheduled for removal in version 6.0.0, ChromaDB remains available for existing deployments requiring specific features. The backend utilizes DuckDB for persistence and offers rich metadata support with complex filtering capabilities.

ChromaDB excels at handling very large collections exceeding 100,000 entries but requires full PyTorch installation and exhibits higher resource consumption. The backend supports multi-modal embeddings and provides advanced query planning for complex searches, though concurrent access performance degrades under load.

### Cloudflare backend enables global serverless deployment

Version 6.2.0's Cloudflare integration combines three services for comprehensive edge computing. **Vectorize** handles distributed vector storage with global replication, **D1** provides SQLite-compatible database functionality at the edge, and **R2** offers object storage for large content and backups.

The serverless architecture automatically scales based on demand, with intelligent caching at edge locations worldwide ensuring sub-50ms query latency globally. Cold start optimization and massive concurrent request handling make this backend ideal for production deployments serving geographically distributed users.

## Memory consolidation system documentation

### Dream-inspired algorithm mimics human memory processes

The consolidation system draws inspiration from human memory consolidation during sleep, implementing multi-stage processing through progressively longer time horizons. This approach naturally organizes memories by importance and recency while discovering creative associations between seemingly unrelated information.

**Automatic organization** occurs through hierarchical structuring from daily to yearly time horizons. The system continuously assesses memory importance based on access patterns, reference frequency, and semantic centrality within the knowledge graph. Related memories cluster automatically based on content similarity, with dynamic tag generation and refinement emerging from content patterns.

### Intelligent compression preserves essential information

The consolidation process employs sophisticated compression techniques that maintain key information while reducing storage overhead. Duplicate detection uses both exact matching and semantic similarity to identify redundant memories, merging them intelligently while preserving unique metadata.

Content summarization creates condensed versions of lengthy memories, particularly useful for conversation transcripts and meeting notes. The system preserves critical details while removing redundant or outdated information, with configurable retention policies ensuring important memories persist appropriately.

### Background processing ensures continuous optimization

Autonomous scheduling allows the consolidation system to run during off-peak hours, with configurable cron-style scheduling for different consolidation levels. Resource management intelligently allocates processing power based on system load, while progress monitoring provides real-time visibility into consolidation status.

The system includes comprehensive health checks that continuously monitor processing queues, identify potential issues, and alert administrators to anomalies. Recovery mechanisms ensure resilience against interruptions, with full state preservation enabling seamless resumption after system restarts.

## API reference with all methods

### MCP protocol implementation follows JSON-RPC 2.0 standards

The service implements the complete MCP specification for tool discovery and invocation:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "store_memory",
    "arguments": {
      "content": "Important architectural decision",
      "tags": ["architecture", "decisions"],
      "metadata": {"importance": "high"}
    }
  }
}
```

Responses include both success results and detailed error information:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Memory stored successfully with ID: abc123"
      }
    ]
  }
}
```

### HTTP/HTTPS endpoints enable REST-style interactions

The standalone HTTP server provides comprehensive REST endpoints:

- **POST /mcp** - Main MCP protocol endpoint
- **GET /mcp/sse** - Server-Sent Events for real-time updates
- **POST /api/tools/list** - Enumerate available tools
- **POST /api/tools/call** - Invoke specific tools
- **GET /api/docs** - Interactive API documentation
- **GET /api/health** - Service health status
- **POST /api/memories** - Store new memories
- **GET /api/memories/search** - Search stored memories
- **DELETE /api/memories/{id}** - Delete specific memory
- **GET /api/stats** - Database statistics
- **POST /api/backup** - Create database backup

### Authentication supports API key and bearer tokens

Production deployments should implement authentication using API keys:

```bash
export MCP_API_KEY="your-secure-api-key"

# Include in requests
curl -X POST http://localhost:8000/api/memories \
  -H "Authorization: Bearer your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{"content": "Secure memory"}'
```

## Usage examples and code snippets

### Python client implementation demonstrates core functionality

```python
import asyncio
from mcp_memory_service.client import MemoryClient

async def memory_operations():
    client = MemoryClient()
    
    # Store memory with tags and metadata
    result = await client.store_memory(
        "Team decided to use PostgreSQL for main database",
        tags=["decisions", "database", "architecture"],
        metadata={"date": "2024-03-15", "priority": "high"}
    )
    
    # Semantic search for related memories
    memories = await client.retrieve_memory(
        "database architecture decisions",
        similarity_threshold=0.8,
        max_results=5
    )
    
    # Time-based recall
    recent = await client.recall_memory("decisions from last week")
    
    # Tag-based operations
    architecture_memories = await client.search_by_tag(["architecture"])
    await client.delete_by_all_tags(["temporary", "draft"])

asyncio.run(memory_operations())
```

### WebSocket connections enable real-time interactions

```python
import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to memory updates
        subscribe = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribe",
            "params": {"events": ["memory_stored", "memory_deleted"]}
        }
        
        await websocket.send(json.dumps(subscribe))
        
        # Listen for real-time updates
        async for message in websocket:
            data = json.loads(message)
            if data.get("method") == "memory_stored":
                print(f"New memory: {data['params']['content']}")

asyncio.run(websocket_client())
```

### Knowledge base patterns structure information effectively

```python
class KnowledgeBase:
    def __init__(self, memory_service):
        self.memory = memory_service
    
    async def store_concept(self, concept, definition, examples=None):
        content = f"Concept: {concept}\nDefinition: {definition}"
        if examples:
            content += f"\nExamples: {', '.join(examples)}"
        
        tags = ["concept", "knowledge", concept.lower().replace(" ", "-")]
        return await self.memory.store_memory(content, {"tags": tags})
    
    async def store_procedure(self, name, steps):
        content = f"Procedure: {name}\n"
        content += "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        
        tags = ["procedure", "howto", name.lower().replace(" ", "-")]
        return await self.memory.store_memory(content, {"tags": tags})
```

## Troubleshooting guide

### Installation issues vary by platform

**PyTorch conflicts** frequently occur on Windows and Intel Macs. The Windows installation script (`scripts/install_windows.py`) automatically resolves CUDA detection and wheel availability issues. For Intel Macs, use `python install.py --force-compatible-deps` to install known-compatible versions, or manually install torch==1.13.1 with matching torchvision and torchaudio versions.

**MCP protocol compatibility** problems typically manifest as missing tools in Claude Desktop. Ensure you're running the latest version with protocol fixes, restart Claude Desktop after configuration changes, and verify that `server.py` contains all required MCP protocol methods. The MCP version should be between 1.0.0 and 2.0.0 for optimal compatibility.

### Database connection errors require specific solutions

**ChromaDB failures** often stem from missing directories or version mismatches. Create the database directory manually if needed, verify ChromaDB version 0.5.23 is installed, and run `python src/chroma_test_isolated.py` to validate the connection independently.

**SQLite-vec issues** typically involve missing dependencies or incorrect configuration. Install sqlite-vec explicitly, set `MCP_MEMORY_STORAGE_BACKEND=sqlite_vec`, and enable ONNX runtime with `MCP_MEMORY_USE_ONNX=1` for CPU-only deployments.

### Performance problems respond to targeted optimization

**High memory usage** indicates the need for backend optimization. Switch to SQLite-vec for 75% memory reduction, reduce batch size to 4 for constrained systems, and consider using the slim Docker image with ONNX runtime instead of PyTorch.

**Slow queries** benefit from similarity threshold adjustment (increase to 0.8+ for faster but more restrictive results), result limit reduction, and database optimization when approaching 10,000 memories. The consolidation system can also help by organizing and compressing older memories.

## Performance tuning recommendations

### Backend selection dramatically impacts resource usage

SQLite-vec excels for collections under 100,000 memories, offering 10x faster startup and minimal memory footprint. ChromaDB suits very large collections but requires significant resources. Cloudflare provides unlimited scalability with global distribution but requires internet connectivity.

### Hardware-specific optimizations maximize efficiency

**Apple Silicon** benefits from Metal Performance Shaders acceleration with `PYTORCH_ENABLE_MPS_FALLBACK=1`. **Windows** systems should use DirectML for AMD GPUs or CUDA for NVIDIA hardware. **CPU-only deployments** achieve best results with ONNX runtime and the slim Docker image.

### Batch size configuration balances speed and memory

Standard systems perform well with batch size 16, while memory-constrained environments should reduce to 4. High-performance systems with ample RAM can increase to 32 or higher. Monitor memory usage during processing to find optimal values for your hardware.

## Integration guides for all clients

### Claude Desktop requires JSON configuration

Add the memory service to `claude_desktop_config.json` located in your Claude application support directory:

```json
{
  "mcpServers": {
    "memory": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-memory-service", "run", "memory"],
      "env": {
        "MCP_MEMORY_SQLITE_PATH": "/path/to/sqlite_vec.db",
        "MCP_MEMORY_BACKUPS_PATH": "/path/to/backups"
      }
    }
  }
}
```

Windows users should use the wrapper script for proper path handling and Python environment activation.

### VS Code integration leverages GitHub Copilot Chat

Enable MCP support in VS Code settings, install the GitHub Copilot Chat extension, and create an `mcp.json` file in your workspace root with the server configuration. The service automatically appears in Copilot Chat after restarting VS Code.

### Cursor IDE supports both global and project configurations

Global configuration in `~/.cursor/mcp.json` makes the memory service available across all projects. Project-specific configuration in `.cursor/mcp.json` limits availability to that workspace. Access Cursor Settings → MCP tab to manage servers through the UI.

### Docker deployment simplifies multi-client coordination

Running the service in Docker with port 8000 exposed allows multiple clients to connect simultaneously. Use volume mounts to persist data across container restarts, and implement API key authentication for production deployments. The standalone mode prevents boot loops while enabling direct HTTP access for testing and development.

The doobidoo/mcp-memory-service represents a sophisticated solution for AI memory management, combining high-performance storage backends with intelligent consolidation algorithms. Its universal compatibility across 13+ AI applications, coupled with flexible deployment options from local SQLite to global Cloudflare distribution, makes it an essential tool for enhancing AI assistant capabilities with persistent, searchable memory.