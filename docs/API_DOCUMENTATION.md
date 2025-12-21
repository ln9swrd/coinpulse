# CoinPulse API Documentation

**Version**: 1.0.0
**Base URL**: `https://coinpulse.sinsi.ai`
**Last Updated**: 2025-12-21

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Signals](#user-signals)
3. [Telegram Linking](#telegram-linking)
4. [Signal Admin](#signal-admin)
5. [Monitoring](#monitoring)
6. [Error Handling](#error-handling)

---

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

### Login

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user@example.com"
  }
}
```

---

## User Signals

### Get User Signal History

```http
GET /api/user/signals
```

**Authentication**: Required

**Query Parameters:**
- `status` (string, optional): Filter by status (`all`, `not_executed`, `executed`, `failed`, `pending`)
- `limit` (number, optional): Number of results (default: 50)
- `offset` (number, optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "signals": [
    {
      "id": 1,
      "signal": {
        "signal_id": "SIGNAL-20251221-001",
        "market": "KRW-XRP",
        "confidence": 85,
        "entry_price": 650,
        "target_price": 682,
        "stop_loss": 637,
        "expected_return": 4.92,
        "reason": "High confidence surge prediction",
        "is_expired": false
      },
      "received_at": "2025-12-21T10:00:00",
      "is_bonus": false,
      "execution_status": "not_executed",
      "executed_at": null,
      "profit_loss": null
    }
  ],
  "count": 10,
  "total": 25,
  "has_more": true
}
```

### Get User Signal Statistics

```http
GET /api/user/signals/stats
```

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "total_received": 25,
  "executed": 12,
  "not_executed": 13,
  "execution_rate": 48.0,
  "total_profit_loss": 150000,
  "win_count": 9,
  "loss_count": 3,
  "win_rate": 75.0,
  "this_month": {
    "received": 8,
    "executed": 4
  }
}
```

### Execute Signal

```http
POST /api/user/signals/{history_id}/execute
```

**Authentication**: Required

**Path Parameters:**
- `history_id` (number): User signal history ID

**Request Body:**
```json
{
  "execution_price": 650.0,
  "notes": "Manual execution"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Signal executed successfully",
  "history": {
    "id": 1,
    "execution_status": "executed",
    "executed_at": "2025-12-21T11:30:00",
    "execution_price": 650.0,
    "notes": "Manual execution"
  }
}
```

### Close Signal Position

```http
POST /api/user/signals/{history_id}/close
```

**Authentication**: Required

**Path Parameters:**
- `history_id` (number): User signal history ID

**Request Body:**
```json
{
  "close_price": 682.0,
  "close_reason": "target_reached",
  "notes": "Target price reached"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Position closed successfully",
  "profit_loss": 492.0,
  "profit_loss_ratio": 4.92,
  "close_reason": "target_reached"
}
```

### Get Signal Performance

```http
GET /api/user/signals/{history_id}/performance
```

**Authentication**: Required

**Path Parameters:**
- `history_id` (number): User signal history ID

**Response:**
```json
{
  "success": true,
  "signal": {
    "market": "KRW-XRP",
    "execution_price": 650,
    "current_price": 670,
    "target_price": 682,
    "stop_loss": 637
  },
  "performance": {
    "profit_loss": 308.0,
    "profit_loss_ratio": 3.08,
    "status": "in_profit",
    "target_progress": 62.5
  }
}
```

---

## Telegram Linking

### Generate Linking Code

```http
POST /api/telegram/link/generate
```

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "code": "123456",
  "expires_at": "2025-12-21T12:15:00",
  "expires_in_minutes": 15
}
```

### Verify Linking Code

```http
POST /api/telegram/link/verify
```

**Authentication**: Not required (public endpoint)

**Request Body:**
```json
{
  "code": "123456",
  "telegram_chat_id": "123456789",
  "telegram_username": "john_doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Telegram account linked successfully",
  "user": {
    "username": "john@example.com",
    "email": "john@example.com",
    "telegram_username": "john_doe"
  }
}
```

### Get Link Status

```http
GET /api/telegram/link/status
```

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "linked": true,
  "telegram_chat_id": "123456789",
  "telegram_username": "john_doe",
  "linked_at": "2025-12-21T10:00:00"
}
```

### Unlink Telegram

```http
POST /api/telegram/link/unlink
```

**Authentication**: Required

**Response:**
```json
{
  "success": true,
  "message": "Telegram account unlinked successfully"
}
```

---

## Signal Admin

**Note**: All admin endpoints require admin authentication.

### Get All Signals

```http
GET /api/admin/signals
```

**Authentication**: Required (Admin)

**Query Parameters:**
- `status` (string, optional): Filter (`all`, `active`, `expired`)
- `limit` (number, optional): Results per page (default: 50)
- `offset` (number, optional): Pagination offset

**Response:**
```json
{
  "success": true,
  "signals": [...],
  "count": 50,
  "total": 150,
  "has_more": true
}
```

### Delete Signal

```http
DELETE /api/admin/signals/{signal_id}
```

**Authentication**: Required (Admin)

**Response:**
```json
{
  "success": true,
  "message": "Signal deleted successfully"
}
```

### Get User Signal Statistics

```http
GET /api/admin/signals/users
```

**Authentication**: Required (Admin)

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "user_id": 1,
      "username": "user@example.com",
      "email": "user@example.com",
      "total_received": 25,
      "executed": 12,
      "execution_rate": 48.0
    }
  ]
}
```

### Get Scheduler Status

```http
GET /api/admin/signals/scheduler/status
```

**Authentication**: Required (Admin)

**Response:**
```json
{
  "success": true,
  "running": true,
  "jobs": [
    {
      "id": "signal_generation",
      "name": "Signal Generation",
      "next_run": "2025-12-21T12:00:00"
    }
  ]
}
```

### Start Scheduler

```http
POST /api/admin/signals/scheduler/start
```

**Authentication**: Required (Admin)

**Response:**
```json
{
  "success": true,
  "message": "Scheduler started successfully"
}
```

### Stop Scheduler

```http
POST /api/admin/signals/scheduler/stop
```

**Authentication**: Required (Admin)

**Response:**
```json
{
  "success": true,
  "message": "Scheduler stopped successfully"
}
```

### Create Manual Signal

```http
POST /api/admin/signals/create
```

**Authentication**: Required (Admin)

**Request Body:**
```json
{
  "market": "KRW-XRP",
  "confidence": 85,
  "entry_price": 650,
  "target_price": 682,
  "stop_loss": 637,
  "reason": "Manual signal for testing",
  "valid_hours": 4
}
```

**Response:**
```json
{
  "success": true,
  "message": "Signal created successfully",
  "signal": {
    "id": 101,
    "signal_id": "MANUAL-20251221-120000",
    "market": "KRW-XRP",
    ...
  }
}
```

### Get Admin Statistics

```http
GET /api/admin/signals/stats
```

**Authentication**: Required (Admin)

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_signals": 150,
    "active_signals": 12,
    "total_users": 25,
    "total_distributions": 450,
    "total_executions": 89,
    "overall_execution_rate": 19.78,
    "last_24h_signals": 8
  }
}
```

---

## Monitoring

### Get Signal Statistics

```http
GET /api/monitoring/signals/stats
```

**Authentication**: Not required

**Response:**
```json
{
  "success": true,
  "total_signals": 150,
  "active_signals": 12,
  "expired_signals": 138,
  "total_distributions": 450,
  "total_executions": 89,
  "execution_rate": 19.78,
  "last_24h": {
    "signals_generated": 8,
    "users_notified": 45
  }
}
```

### Get Recent Signals

```http
GET /api/monitoring/signals/recent
```

**Authentication**: Not required

**Response:**
```json
{
  "success": true,
  "signals": [
    {
      "signal_id": "SIGNAL-20251221-001",
      "market": "KRW-XRP",
      "confidence": 85,
      "entry_price": 650,
      "distributed_to": 15,
      "executed_count": 3,
      "execution_rate": 20.0,
      "status": "active",
      "created_at": "2025-12-21T10:00:00"
    }
  ],
  "count": 20
}
```

### Get Top Performers

```http
GET /api/monitoring/signals/top-performers
```

**Authentication**: Not required

**Response:**
```json
{
  "success": true,
  "signals": [
    {
      "signal_id": "SIGNAL-20251220-001",
      "market": "KRW-BTC",
      "confidence": 90,
      "entry_price": 50000000,
      "distributed_to": 20,
      "executed_count": 15,
      "execution_rate": 75.0,
      "created_at": "2025-12-20T14:00:00"
    }
  ],
  "count": 10
}
```

---

## Error Handling

All API endpoints follow a consistent error response format:

### Error Response Format

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

### Common Error Messages

**Authentication Errors:**
```json
{
  "success": false,
  "error": "No token provided"
}
```

```json
{
  "success": false,
  "error": "Invalid or expired token"
}
```

**Validation Errors:**
```json
{
  "success": false,
  "error": "Missing required field: market"
}
```

**Resource Not Found:**
```json
{
  "success": false,
  "error": "Signal not found"
}
```

**Business Logic Errors:**
```json
{
  "success": false,
  "error": "Signal already executed"
}
```

```json
{
  "success": false,
  "error": "Signal has expired"
}
```

---

## Rate Limiting

- **Unauthenticated requests**: 100 requests per hour per IP
- **Authenticated requests**: 1000 requests per hour per user
- **Admin requests**: Unlimited

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640094000
```

---

## Changelog

### Version 1.0.0 (2025-12-21)
- Initial API release
- User signal management endpoints
- Telegram account linking
- Admin panel endpoints
- Signal execution tracking
- Real-time performance monitoring

---

## Support

For API support, contact: support@sinsi.ai
Documentation: https://coinpulse.sinsi.ai/docs
