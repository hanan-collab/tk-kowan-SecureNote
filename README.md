# SecureNote

A serverless application for creating secure, self-destructing notes with password protection.

## Overview

SecureNote enables users to create encrypted notes that automatically self-destruct after a specified expiration time or immediately after being read. Notes are securely stored in Amazon DynamoDB and are automatically removed using AWS EventBridge Scheduler, ensuring timely cleanup and minimal data retention.

## Frontend Application

The SecureNote frontend is implemented as a **single-page static web application** using a single main file, `index.html`. The application exposes two primary routes:

1. `/` — **Create Note**  
   Users can write a secure note and define a password required to access it. After the note is created, the user receives the generated `UUID`, a `read link`, and the `expiration date`, which can then be shared with the intended recipient.

2. `/read/{uuid}` — **Read Note**  
   Users provide the corresponding `UUID` and password to access the secure note. Once the note is successfully read or reaches its expiration time, it is automatically deleted from the system.

The frontend application:
- Does not use any JavaScript framework (e.g., React, Vue)
- Relies on **simple client-side routing**
- Communicates directly with the backend through a **REST API (Amazon API Gateway)**
- `utils/encryption.js` implements client-side encryption to ensure that note contents are encrypted prior to transmission to the backend API.

This approach was chosen to:
- Simplify the deployment process
- Reduce dependency complexity
- Enable direct hosting on static hosting services such as **Amazon S3**


## Frontend Deployment (Static Hosting)

The frontend can be deployed using the following approaches:

### Option 1 — Local / Development
Open the `index.html` file directly in a browser or serve it using a simple static HTTP server.

### Option 2 — Amazon S3 Static Website Hosting (Recommended)

General steps:
1. Create an S3 bucket
2. Enable **Static Website Hosting**
3. Upload the `index.html` file and `util/encryption.js` file
4. Configure the bucket policy to allow public read access
5. HTTPS integration using **Amazon CloudFront** with S3 bucket domain

Currently the application can be accessed from:
```
https://d15kh86ub0unax.cloudfront.net/
```

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
| `ALLOWED_ORIGIN` | CORS Allowed Origin |

## API: Read Note

### Endpoint

`POST /read/{id}`

### Path Parameters

| Parameter | Type | Required | Description |
|----------|-------------|----------|-------------|
|`id`      |string       |Yes       |The unique UUID of the note to retrieve |

### Response

**Sucess (200)**
```json
{
  "message": "Note retrieved and destroyed successfully",
  "content": "encrypted-content-here",
  "password": "hashed-password-from-db",
  "salt": "random-salt",
  "created_at": 1766902326,
  "ttl": 1766904126
}
```

**Bot/Preview Detected (200)**
```json
{
  "message": "Link Preview",
  "content": "Hidden."
}
```

**Error (400): Bad Request**
```json
{
  "message": "Note ID is missing"
}
```

**Error (404): Not Found**
```json
{
  "message": "Note not found or already destroyed."
}
```

**Error (500): Internal Server Error**
```json
{
  "message": "Internal Server Error: <error_details>"
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `NOTES` | DynamoDB table name |
| `ALLOWED_ORIGIN` | CORS Allowed Origin |

## Deployment API

This section describes the steps required to deploy the SecureNotes backend using AWS DynamoDB, AWS Lambda, and Amazon API Gateway.

---

### 1. Database Setup (Amazon DynamoDB)

1. Create a DynamoDB table with the following configuration:

   * **Table name:** `SecureNotes`
   * **Partition key:** `note_id` (String)
   * **Table class:** DynamoDB Standard
   * **Capacity mode:** On-demand (optional, recommended for variable workloads)

2. After the table is created, enable **Time to Live (TTL)**:

   * Navigate to **Additional settings** → **Time to Live (TTL)**
   * Enable TTL and set the attribute name to `ttl`

   This configuration ensures that notes are automatically deleted after their expiration time.

---

### 2. Backend Functions (AWS Lambda)

1. For each function defined in the `services` directory:

   * Create a separate AWS Lambda function.
   * Assign the execution role to **LabRole** instead of the default role.

2. Configure each Lambda function according to its documentation:

   * Set the required **environment variables**.
   * Adjust runtime settings (e.g., timeout, memory) if needed.

3. Repeat this process for all functions in the `services` directory to ensure full backend functionality.

---

### 3. API Layer (Amazon API Gateway)

1. Create a **REST API** in Amazon API Gateway with the following settings:

   * **API name:** `SecureNotes`
   * **Endpoint type:** Regional

2. For each Lambda function:

   * Create a corresponding API resource (e.g., `/create`, `/read/{id}`).
   * Add a **POST** method for each resource.
   * Enable **Lambda Proxy Integration** and link the method to the appropriate Lambda function.

3. Enable **CORS** on all API resources to allow cross-origin requests.

4. Deploy the API:

   * Create a deployment stage (e.g., `prod`).
   * Note the **Invoke URL**, which will be used by the frontend or client applications to access the API.

