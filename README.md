# Stories-Teller Server  

This repository contains the **server-side core** of the **Stories-Teller** project.  
The server coordinates interactions between **clients** and the **generator app**, managing task distribution and data exchange.  

## 🚀 Features  
- Accepts connections from **clients** via WebSocket (`/ws/client`).  
- Accepts connections from the **generator app** via WebSocket (`/ws/admin`).  
- Receives generation requests from clients via HTTPS (`/upload`).  
- Notifies the generator app about new tasks in real time.  
- Provides endpoints for the generator to upload/download files (`/uploads/{filename}`, `/descriptions/{filename}`).  
- Collects generated results from the generator (`/describe`) and makes them available to clients.  

## 🛠 Tech Stack  
- **WebSocket** – communication with clients and the generator
- **HTTPS** – handling uploads, results, and file access
- **FastAPI** - endpoints, structure, and layout
- **Pydantic** – data validation and secure message models 

## 🔄 Workflow  

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Generator

    Client->>Server: Connect via WebSocket (/ws/client)
    Client->>Server: Upload generation request (/upload)
    Server->>Generator: Notify new task (/ws/admin)

    Generator->>Server: Download image (/uploads/{filename})
    Generator->>Server: Download text (/descriptions/{filename})

    Generator->>Server: Upload generated story (/describe)
    Server->>Client: Notify task completed
    Client->>Server: Retrieve story (/descriptions/{filename})
