# Organization Management Service

A robust MVP for managing multi-tenant organizations using FastAPI and MongoDB. This service implements a dynamic collection architecture where each organization gets its own isolated MongoDB collection.

## Project Highlights

- **Service/Repository pattern** with class-based service layer for modularity and testability
- **Master Collection (`organizations`)** stores global metadata (name, email, password_hash, collection_name)
- **Dynamic Tenant Collections (`org_<name>`)** created automatically per organization for data isolation
- **Async MongoDB driver (motor)** for non-blocking database operations
- **JWT Authentication** with bcrypt password hashing for secure admin access
- **Collection migration** automatically renames tenant collections when organization names change

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB (local or remote instance)
- pip

### Installation

1. **Create virtual environment and install dependencies**

   ```bash
   python3 -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   Create a `.env` file in the project root:

   ```ini
   MONGO_URI=mongodb://localhost:27017
   SECRET_KEY=your-secret-key-here-change-in-production
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   JWT_ALGORITHM=HS256
   MASTER_DB_NAME=org_master
   ```

   **Note:** Make sure MongoDB is running and accessible at the `MONGO_URI` specified.

3. **Run the API server**

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://127.0.0.1:8000`

4. **Explore API documentation**

   - Interactive Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### 1. Create Organization
- **POST** `/org/create`
- **Description:** Creates a new organization with admin credentials and automatically creates a tenant collection
- **Request Body:**
  ```json
  {
    "organization_name": "Acme Corp",
    "email": "admin@acme.com",
    "password": "securepassword123"
  }
  ```
- **Response:** Organization details with ID and collection name (201 Created)

### 2. Get Organization
- **GET** `/org/get?organization_name=Acme%20Corp`
- **Description:** Retrieves organization metadata by name
- **Query Parameters:** `organization_name` (required)
- **Response:** Organization details (200 OK) or 404 if not found

### 3. Admin Login
- **POST** `/admin/login`
- **Description:** Authenticates admin and returns JWT access token
- **Request Body:**
  ```json
  {
    "email": "admin@acme.com",
    "password": "securepassword123"
  }
  ```
- **Response:** JWT token with `admin_email` and `organization_name` in payload

### 4. Update Organization
- **PUT** `/org/update`
- **Description:** Updates organization metadata (name, email, password). Requires JWT authentication. Automatically migrates tenant collection if name changes.
- **Authentication:** Required (Bearer token)
- **Request Body:**
  ```json
  {
    "organization_name": "New Name",
    "email": "newemail@acme.com",
    "password": "newpassword123"
  }
  ```
  All fields are optional. The current organization is identified from the JWT token.

### 5. Delete Organization
- **DELETE** `/org/delete?organization_name=Acme%20Corp`
- **Description:** Deletes organization and its tenant collection. Requires JWT authentication.
- **Authentication:** Required (Bearer token)
- **Query Parameters:** `organization_name` (required, must match JWT)
- **Response:** 204 No Content on success

## Architecture

### Database Structure

1. **Master Collection (`organizations`)**
   - Stores organization metadata: `name`, `email`, `password_hash`, `collection_name`
   - Used for authentication and organization lookup
   - Located in the master database (`org_master` by default)

2. **Tenant Collections (`org_<organization_name>`)**
   - Dynamic collections created per organization
   - Automatically created when an organization is registered
   - Automatically renamed when organization name changes
   - Automatically dropped when organization is deleted

### Design Patterns

- **Controller-Service-Repository Pattern:** Routes handle HTTP concerns, services contain business logic, database operations are abstracted
- **Class-based Services:** All business logic is encapsulated in service classes for modularity and testability
- **Multi-tenant Architecture:** Each organization has isolated data through separate collections

### Security Features

- **Password Hashing:** bcrypt with automatic salt generation
- **JWT Authentication:** Tokens include `admin_email` and `organization_name` for authorization
- **Input Validation:** Pydantic schemas enforce constraints (email format, password length, name length)
- **Error Handling:** Proper HTTP status codes (400, 401, 404) with descriptive error messages

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Environment configuration
│   └── database.py        # MongoDB connection management
├── models/
│   └── organization.py    # Pydantic schemas
├── routes/
│   ├── org_routes.py      # Organization endpoints
│   └── admin_routes.py    # Admin authentication endpoints
├── services/
│   ├── organization_service.py  # Organization business logic
│   └── admin_service.py         # Admin authentication logic
└── utils/
    ├── dependencies.py    # FastAPI dependencies (JWT validation)
    ├── jwt_handler.py     # JWT encoding/decoding
    └── security.py        # Password hashing utilities
```

## Testing the API

### Example: Create Organization

```bash
curl -X POST "http://127.0.0.1:8000/org/create" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Acme Corp",
    "email": "admin@acme.com",
    "password": "securepass123"
  }'
```

### Example: Admin Login

```bash
curl -X POST "http://127.0.0.1:8000/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "securepass123"
  }'
```

### Example: Update Organization (Authenticated)

```bash
curl -X PUT "http://127.0.0.1:8000/org/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "organization_name": "Acme Corporation",
    "email": "newadmin@acme.com"
  }'
```

## Trade-offs & Considerations

- **Collection per tenant:** Provides excellent data isolation and easy per-org backups, but may hit MongoDB namespace limits at very large scale (thousands of organizations)
- **Async operations:** Motor driver enables non-blocking I/O for better concurrency
- **Service layer:** Centralizes business logic, making it easier to test and maintain

## Future Enhancements

- Add organization-specific domain models inside tenant collections
- Implement refresh tokens for better security
- Add role-based access control (beyond single admin)
- Comprehensive test suite (pytest + HTTPX)
- CI/CD pipeline with linting and automated tests
- Rate limiting and request throttling
- Audit logging for organization operations

## High-Level Diagram
```mermaid
graph TD
    %% Actors
    Client([Client / Frontend])
    Admin([Admin User])

    %% API Layer
    subgraph "API Layer (FastAPI)"
        Routes["Routes / Controllers<br/>(org_routes.py)"]
        Auth["Auth System<br/>(JWT & Dependencies)"]
    end

    %% Business Logic Layer
    subgraph "Service Layer (Class-Based)"
        OrgService["OrganizationService Class<br/>(Business Logic)"]
        AuthService["AuthService Class<br/>(Login Logic)"]
    end

    %% Data Access Layer
    subgraph "Data Access Layer"
        DBManager["DatabaseManager Class<br/>(Connection Handling)"]
    end

    %% Database Layer
    subgraph "MongoDB Instance"
        MasterDB[("Master Database<br/>(Metadata & Admin Users)")]
        
        subgraph "Dynamic Tenant Collections"
            Org1[("Org_A Collection")]
            Org2[("Org_B Collection")]
        end
    end

    %% Relationships
    Client -->|HTTP Requests| Routes
    Admin -->|Login Request| Auth
    
    Routes -->|Calls| OrgService
    Auth -->|Calls| AuthService
    
    OrgService -->|Uses| DBManager
    AuthService -->|Uses| DBManager
    
    DBManager -->|Reads/Writes| MasterDB
    DBManager -->|Creates/Manages| Org1
    DBManager -->|Creates/Manages| Org2

    %% Styles
    style MasterDB fill:#f9f,stroke:#333,stroke-width:2px
    style Org1 fill:#bbf,stroke:#333,stroke-width:2px
    style Org2 fill:#bbf,stroke:#333,stroke-width:2px
    style DBManager fill:#ff9,stroke:#333,stroke-width:2px
    ```
