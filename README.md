# Microservices E-commerce Backend

A production-style backend built with **FastAPI**, **PostgreSQL**, **Docker**, and **JWT authentication** — split across three independent microservices.

---

## Architecture

```
[Client / Swagger UI]
        |
        +---> Auth Service    (port 8001)  — register, login, token verification
        |
        +---> Catalog Service (port 8002)  — products CRUD
        |
        +---> Orders Service  (port 8003)  — place and track orders
                |                   |
          [catalog-db]         [orders-db]        [auth-db]
          PostgreSQL            PostgreSQL          PostgreSQL
```

Each service has its **own isolated PostgreSQL database**. Services communicate with each other over HTTP using Docker's internal network.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt (passlib 1.7.4 + bcrypt 4.0.1) |
| Containerization | Docker + Docker Compose |
| Inter-service calls | httpx (async HTTP client) |

---

## Project Structure

```
ecommerce-microservices/
├── docker-compose.yml
├── README.md
├── auth-service/
│   ├── main.py           ← FastAPI app, all routes
│   ├── auth.py           ← JWT creation/decoding, password hashing
│   ├── models.py         ← SQLAlchemy User model
│   ├── schemas.py        ← Pydantic request/response shapes
│   ├── database.py       ← DB engine and session
│   ├── requirements.txt
│   └── Dockerfile
├── catalog-service/
│   ├── main.py
│   ├── models.py         ← Product model with composite index
│   ├── schemas.py
│   ├── database.py
│   ├── requirements.txt
│   └── Dockerfile
└── orders-service/
    ├── main.py
    ├── models.py         ← Order + OrderItem models
    ├── schemas.py
    ├── database.py
    ├── requirements.txt
    └── Dockerfile
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Git](https://git-scm.com/)

---

## Running Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ecommerce-microservices.git
cd ecommerce-microservices

# 2. Start all services
docker-compose up --build

# 3. To stop
docker-compose down

# 4. To stop AND wipe all database data
docker-compose down -v
```

---

## API Docs

FastAPI auto-generates interactive docs for each service:

| Service | URL |
|---|---|
| Auth | http://localhost:8001/docs |
| Catalog | http://localhost:8002/docs |
| Orders | http://localhost:8003/docs |

---

## Testing the Full Flow

### Step 1 — Register a user
```bash
curl -X POST 'http://localhost:8001/register' \
  -H 'Content-Type: application/json' \
  -d '{"email": "test@gmail.com", "password": "test", "full_name": "Test User"}'
```

### Step 2 — Login and get a token
```bash
curl -X POST 'http://localhost:8001/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=test@gmail.com&password=test'
```
Copy the `access_token` from the response.

### Step 3 — Add a product (replace TOKEN with your token)
```bash
curl -X POST 'http://localhost:8002/products' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"name": "Laptop", "description": "Fast laptop", "price": 999.99, "stock": 10, "category": "electronics"}'
```

### Step 4 — Browse products (no token needed)
```bash
curl 'http://localhost:8002/products'

# With search
curl 'http://localhost:8002/products?search=laptop'

# With category filter
curl 'http://localhost:8002/products?category=electronics'
```

### Step 5 — Place an order (replace TOKEN with your token)
```bash
curl -X POST 'http://localhost:8003/orders' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"items": [{"product_id": 1, "quantity": 2}]}'
```

### Step 6 — View your orders
```bash
curl 'http://localhost:8003/orders' \
  -H 'Authorization: Bearer TOKEN'
```

---

## Using Swagger UI (Browser)

1. Open http://localhost:8002/docs (or 8003)
2. Click **Authorize 🔒** (top right)
3. Enter your **username** (email) and **password** in the OAuth2 form
4. Click **Authorize** → **Close**
5. All endpoints will now automatically include your token

> **Note:** The Authorize form on ports 8002 and 8003 calls `http://localhost:8001/login` directly — this works because CORS is enabled on the Auth Service.

---

## Key Concepts

**JWT Authentication across services**
The Catalog and Orders services do not have their own JWT secret. Instead, they forward the token to Auth Service's `/verify-token` endpoint. This keeps auth logic in one place.

**DB isolation**
Each service has its own PostgreSQL database (`authdb`, `catalogdb`, `ordersdb`). Services never query each other's databases directly — they only communicate via HTTP.

**Health checks**
`docker-compose.yml` uses `pg_isready` health checks so services only start after their database is fully ready, avoiding connection errors on startup.

**Data snapshots in Orders**
When an order is placed, `product_name` and `unit_price` are copied into the order. This means historical orders stay accurate even if a product's name or price changes later.

---

## Known Dependency Fix

If you see `AttributeError: module 'bcrypt' has no attribute '__about__'`, it means bcrypt version is too new for passlib. The `requirements.txt` in auth-service pins the correct versions:

```
passlib==1.7.4
bcrypt==4.0.1
```

---

## Deploying to Render (Free Hosting)

1. Push to GitHub: `git push origin main`
2. Go to [render.com](https://render.com) → sign in with GitHub
3. Create a **PostgreSQL** database for each service (free 90-day tier)
4. Create a **Web Service** for each microservice:
   - Select your repo
   - Set **Root Directory** to `auth-service` / `catalog-service` / `orders-service`
   - Docker runtime is auto-detected
   - Add environment variables (`DATABASE_URL`, `SECRET_KEY`, `AUTH_SERVICE_URL`, etc.)
5. Deploy

---

## API Reference

### Auth Service — port 8001
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/register` | No | Register new user |
| POST | `/login` | No | Login, returns JWT |
| GET | `/verify-token` | Yes | Validate a token (used by other services) |
| GET | `/me` | Yes | Get current user profile |

### Catalog Service — port 8002
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/products` | No | List products (supports `search`, `category`, `skip`, `limit`) |
| GET | `/products/{id}` | No | Get single product |
| POST | `/products` | Yes | Create product |
| PUT | `/products/{id}` | Yes | Update product |
| DELETE | `/products/{id}` | Yes | Delete product |

### Orders Service — port 8003
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/orders` | Yes | Place an order |
| GET | `/orders` | Yes | List your orders |
| GET | `/orders/{id}` | Yes | Get a specific order |
| PATCH | `/orders/{id}/status` | Yes | Update order status |