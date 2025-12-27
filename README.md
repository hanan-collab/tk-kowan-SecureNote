# SecureNote

A serverless application for creating secure, self-destructing notes with password protection.

## Overview

SecureNote enables users to create encrypted notes that automatically self-destruct after a specified expiration time or immediately after being read. Notes are securely stored in Amazon DynamoDB and are automatically removed using AWS EventBridge Scheduler, ensuring timely cleanup and minimal data retention.

## API: Create Note

### Endpoint

`POST /create`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | The encrypted note content |
| `password` | string | Yes | Hashed password for note access |
| `salt` | string | Yes | Salt used for password hashing |
| `ttl` | integer | No | Time-to-live in minutes (default: 60) |

### Example Request

```json
{
  "content": "encrypted-content-here",
  "password": "hashed-password",
  "salt": "random-salt",
  "ttl": 30
}
```

### Response

**Success (201)**
```json
{
  "message": "Note created successfully",
  "note_id": "uuid-here",
  "link": "https://app.example.com/read/uuid-here",
  "expires_at": 1703721600
}
```

**Error (400)**
```json
{
  "message": "Content is required"
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `NOTES` | DynamoDB table name |
| `CLEANUP_TARGET_ARN` | ARN of the cleanup Lambda function |
| `SCHEDULER_ROLE_ARN` | IAM role ARN for EventBridge Scheduler |
| `APP_BASE_URL` | Base URL for generating shareable links |

## API: Read Note

### Endpoint

`GET /read/{id}`

### Path Parameters

| Parameter | Type | Required | Description |
|----------|-------------|----------|-------------|
|`id`      |string       |Yes       |The unique UUID of the note to retrieve |

### Response

**Sucess (200)**
```json
{
  "message": "Note retrieved and destroyed successfully",
  "content": "U2FsdGVkX1+...",
  "password": "hashed-password-string",
  "salt": "random-salt-string"
}
```

**Bot/Preview Detected (200)**
```json
{
  "message": "Secure Note Link Preview",
  "content": "This content is hidden for security reasons. Please open the link directly in your browser."
}
```

**Error (400)**
```json
{
  "message": "Note not found or already destroyed."
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `NOTES` | DynamoDB table name |