# Process Monitor Application

## Documentation

### 1. Brief Architecture Overview

The **Process Monitor Application** is a system that monitors running processes on machines and displays them in a web interface.  
It consists of three main components:

- **Agent (Executable)**

  - A lightweight Python program (`agent.py`) compiled to a standalone executable using PyInstaller.
  - Collects details about running processes:
    - Process name, PID
    - CPU and Memory usage
    - Parent-child process relationships
    - Hostname of the machine
  - Sends this data to the backend via REST API.
  - Runs by double-clicking, no installation required.

- **Backend (Django + Django REST Framework + WebSockets)**

  - Provides REST API endpoints for agents and frontend.
  - Stores process data in a SQLite database.
  - Includes authentication: each agent must use a valid API key to upload data.
  - Maintains historical snapshots of processes, with hostname identification.
  - Supports **WebSockets** for real-time data streaming to frontend.

- **Frontend (HTML, CSS, JavaScript)**
  - Displays process data in a **tree-like expandable view** (parent and subprocesses).
  - Shows the latest snapshot with timestamp and hostname.
  - Allows browsing of historical snapshots.
  - Provides **search functionality** to quickly find processes by name or PID.
  - Supports **multiple charts** (CPU, memory, process count, per-host statistics).
  - Updates live using **WebSockets** for real-time monitoring.
  - Responsive and clean UI.

**Flow**:

1. Agent collects process information and sends it securely to the backend.
2. Backend validates the API key, stores data in SQLite, and provides it via REST APIs or WebSocket channels.
3. Frontend queries APIs and subscribes to WebSockets to render:
   - Latest snapshot (auto-refresh via WebSocket)
   - Historical snapshots
   - Process hierarchy with expandable/collapsible nodes
   - Search results
   - Multiple charts for visualization (CPU/memory/time-series trends)

---

### 2. API Specifications

**Base URL**

```
127.0.0.1:8000/api/
```

**Endpoints**

- **POST /process-snapshots/**

  - **Description**: Upload process snapshot data from agent.
  - **Authentication**: API Key required in headers (`Authorization: Api-Key <key>`).
  - **Request Example**:
    ```json
    {
      "hostname": "MACHINE-01",
      "snapshot_time": "2025-08-22T09:15:00Z",
      "processes": [
        {
          "pid": 100,
          "name": "explorer.exe",
          "cpu": 2.5,
          "memory": "150MB",
          "parent_pid": null,
          "children": [
            {
              "pid": 200,
              "name": "notepad.exe",
              "cpu": 1.2,
              "memory": "50MB",
              "parent_pid": 100
            }
          ]
        }
      ]
    }
    ```
  - **Response Example**:
    ```json
    { "message": "Snapshot uploaded successfully." }
    ```

- **GET /hosts/**

  - **Description**: Retrieve list of hosts that have uploaded data.
  - **Response Example**:
    ```json
    [{ "hostname": "MACHINE-01" }, { "hostname": "MACHINE-02" }]
    ```

- **GET /process-snapshots/latest/**

  - **Description**: Retrieve the latest snapshot for each host.
  - **Response Example**:
    ```json
    {
      "hostname": "MACHINE-01",
      "snapshot_time": "2025-08-22T09:15:00Z",
      "processes": [...]
    }
    ```

- **GET /process-snapshots/list/**

  - **Description**: Retrieve a list of available snapshots (with timestamps).
  - **Query Parameters**:
    - `hostname` (optional) → filter by host
  - **Response Example**:
    ```json
    [
      {
        "snapshot_id": 1,
        "hostname": "MACHINE-01",
        "timestamp": "2025-08-22T09:15:00Z"
      },
      {
        "snapshot_id": 2,
        "hostname": "MACHINE-01",
        "timestamp": "2025-08-22T09:30:00Z"
      }
    ]
    ```

- **GET /process-snapshots/{snapshot_id}/**

  - **Description**: Retrieve details of a specific snapshot.
  - **Response Example**:
    ```json
    {
      "snapshot_id": 2,
      "hostname": "MACHINE-01",
      "timestamp": "2025-08-22T09:30:00Z",
      "processes": [...]
    }
    ```

- **GET /process-snapshots/series/**

  - **Description**: Retrieve a series of snapshots for analysis and charts.
  - **Query Parameters**:
    - `hostname` → required
    - `limt` → optional limit range

- **WebSocket /ws/process-snapshots/**
  - **Description**: Real-time updates of process snapshots pushed to connected clients.

---

### 3. Assumptions Made

1. Agent runs with sufficient privileges to collect process data.
2. Backend uses **SQLite** for simplicity but can be scaled with PostgreSQL/MySQL.
3. API Key authentication is required for agents uploading data; frontend reads data via REST/WebSockets.
4. WebSocket channel is secured (production-ready setup should use WSS + authentication).
5. Process hierarchy is reconstructed using parent-child PID relationships.
6. Time is stored in **UTC** for consistency.
7. Charts and search functionality are client-side and powered by JavaScript.

---

### 4. Setup Instructions

#### Backend (Django + DRF + Channels)

1. Navigate to backend folder:
   ```bash
   cd backend
   ```
2. Create virtual environment and install requirements:

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows

   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Create a superuser (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```
5. Setup API Key:
   ```bash
   python manage.py create_apikey
   ```
   Copy and paste the output in **agent/agent_config.json** as the value of api_key
6. Run the server:
   ```bash
   python manage.py runserver
   ```

---

#### Agent

1. Navigate to `agent/` folder.
   ```bash
   cd agent
   ```
2. Configure `agent.py` with backend endpoint and API key.
3. Run directly with Python:
   ```bash
   python agent.py
   ```
4. Or run the compiled executable:
   ```bash
   ./dist/agent    # Linux/Mac
   dist\agent.exe  # Windows
   ```
5. The agent collects data and sends it to the backend periodically.

---

#### Frontend

1. Navigate to frontend folder:
   ```bash
   cd frontend
   ```
2. Open `index.html` in a browser.
3. The frontend fetches process data from backend APIs and subscribes to WebSockets:
   - Displays **latest snapshot** in real-time.
   - Allows **searching processes** by name/PID.
   - Renders **historical snapshots**.
   - Visualizes data with **multiple charts** (CPU, memory, number of processes over time).

---

### 5. Future Enhancements

- Role-based access control for frontend users.
- Configurable alerting system (CPU/memory thresholds).
- Advanced filtering (by host, by process type, by resource usage).
- Export snapshots as CSV/JSON.
- Cloud deployment with multi-agent orchestration.
