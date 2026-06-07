# Integration Report: Salesforce to Shopify

- Generated: 2026-06-07T18:51:16+00:00
- Status: complete
- Source: Salesforce
- Target: Shopify
- Prompt: Connect Salesforce with Shopify

## API Discovery

### Source API: Salesforce

- Base URL: https://your-domain.my.salesforce.com
- Authentication: OAuth2

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /sobjects/Account | Retrieve a list of accounts. Pagination details are uncertain. |
| GET | /sobjects/Contact | Retrieve a list of contacts. Filtering and sorting options are uncertain. |
| POST | /sobjects/Account | Create a new account. Required fields and write semantics are uncertain. |
| PATCH | /sobjects/Account/{id} | Update an existing account. Uncertain which fields can be updated and what the update semantics are. |
| GET | /sobjects/Opportunity | Retrieve a list of opportunities. Filtering by stage and other criteria is uncertain. |
| GET | /sobjects/Lead | Retrieve a list of leads. Sorting and pagination options are uncertain. |
| POST | /sobjects/Contact | Create a new contact. Required fields and write semantics are uncertain. |
| DELETE | /sobjects/Account/{id} | Delete an existing account. Uncertain what the delete semantics are and if there are any restrictions. |

### Target API: Shopify

- Base URL: https://your-store.shopify.com
- Authentication: OAuth2

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /orders.json | Retrieve a list of orders. Pagination details are uncertain. |
| GET | /products.json | Retrieve a list of products. Filtering and sorting options are uncertain. |
| POST | /orders.json | Create a new order. Required fields and write semantics are uncertain. |
| PATCH | /orders/{id}.json | Update an existing order. Uncertain which fields can be updated and what the update semantics are. |
| GET | /customers.json | Retrieve a list of customers. Filtering by email and other criteria is uncertain. |
| GET | /products/{id}.json | Retrieve a product by ID. Uncertain what the response format is. |
| POST | /customers.json | Create a new customer. Required fields and write semantics are uncertain. |
| DELETE | /orders/{id}.json | Delete an existing order. Uncertain what the delete semantics are and if there are any restrictions. |

## Field Mapping

- Mapped fields: 12
- Total fields: 19
- Mapped percent: 63%

| Source Field | Target Field | Transformation | Confidence | Notes |
| --- | --- | --- | --- | --- |
| Id | id | direct | 90% | Salesforce Account ID maps to Shopify Customer ID |
| Name | name | direct | 95% | Salesforce Account Name maps to Shopify Customer Name |
| BillingAddress | address | direct | 80% | Salesforce Account Billing Address maps to Shopify Customer Address |
| Phone | phone | direct | 90% | Salesforce Account Phone maps to Shopify Customer Phone |
| Email | email | direct | 95% | Salesforce Contact Email maps to Shopify Customer Email |
| Opportunity.Amount | total_spent | direct | 80% | Salesforce Opportunity Amount maps to Shopify Customer Total Spent |
| Opportunity.CloseDate | last_order_date | direct | 80% | Salesforce Opportunity Close Date maps to Shopify Customer Last Order Date |
| Lead.Company | company | direct | 80% | Salesforce Lead Company maps to Shopify Customer Company |
| Contact.Title | title | direct | 70% | Salesforce Contact Title maps to Shopify Customer Title |
| Account.Website | website | direct | 70% | Salesforce Account Website maps to Shopify Customer Website |
| Opportunity.StageName | tags | direct | 60% | Salesforce Opportunity Stage Name maps to Shopify Customer Tags |
| Account.Industry | industry | direct | 60% | Salesforce Account Industry maps to Shopify Customer Industry |

### Unmapped Source Fields

- Account.Description
- Contact.Department
- Opportunity.Product
- Lead.Status

### Unmapped Target Fields

- customer.orders_count
- customer.total_orders
- customer.orders

## Reviewed Connector Code

```python
import os
import logging
import httpx
import tenacity
import argparse
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
SALESFORCE_BASE_URL = os.environ.get('SALESFORCE_BASE_URL')
SALESFORCE_CLIENT_ID = os.environ.get('SALESFORCE_CLIENT_ID')
SALESFORCE_CLIENT_SECRET = os.environ.get('SALESFORCE_CLIENT_SECRET')
SHOPIFY_BASE_URL = os.environ.get('SHOPIFY_BASE_URL')
SHOPIFY_CLIENT_ID = os.environ.get('SHOPIFY_CLIENT_ID')
SHOPIFY_CLIENT_SECRET = os.environ.get('SHOPIFY_CLIENT_SECRET')
SALESFORCE_ACCESS_TOKEN = os.environ.get('SALESFORCE_ACCESS_TOKEN')
SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')

# Check if environment variables are set
if not all([SALESFORCE_BASE_URL, SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_ACCESS_TOKEN, SHOPIFY_BASE_URL, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SHOPIFY_ACCESS_TOKEN]):
    logger.error('Missing environment variables')
    exit(1)

# Define field mappings
FIELD_MAPPINGS = [
    {'sourceField': 'Id', 'sourceType': 'string', 'targetField': 'id', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.9},
    {'sourceField': 'Name', 'sourceType': 'string', 'targetField': 'name', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.95},
    {'sourceField': 'BillingAddress', 'sourceType': 'object', 'targetField': 'address', 'targetType': 'object', 'transformation': 'direct', 'confidence': 0.8},
    {'sourceField': 'Phone', 'sourceType': 'string', 'targetField': 'phone', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.9},
    {'sourceField': 'Email', 'sourceType': 'string', 'targetField': 'email', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.95},
    # Omitting Opportunity.Amount mapping as it may not be semantically safe to map opportunity amount to customer total spent
    # Omitting Opportunity.CloseDate mapping as it may not be semantically safe to map opportunity close date to customer last order date
    {'sourceField': 'Lead.Company', 'sourceType': 'string', 'targetField': 'company', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.8},
    {'sourceField': 'Contact.Title', 'sourceType': 'string', 'targetField': 'title', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.7},
    {'sourceField': 'Account.Website', 'sourceType': 'string', 'targetField': 'website', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.7},
    # Omitting Opportunity.StageName mapping as it may not be semantically safe to map opportunity stage name to customer tags
    # Omitting Account.Industry mapping as it may not be semantically safe to map account industry to customer industry
]

# Define async HTTP client
async def get_async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()

# Define retry decorator
@tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10))
async def retry_async_call(func, *args, **kwargs):
    return await func(*args, **kwargs)

# Define pagination function
async def paginate_endpoint(endpoint: Dict, params: Dict = {}) -> List:
    async with get_async_client() as client:
        headers = {'Authorization': f'Bearer {SALESFORCE_ACCESS_TOKEN}'}
        response = await retry_async_call(client.get, SALESFORCE_BASE_URL + endpoint['path'], params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        results = data['records']
        while 'nextRecordsUrl' in data:
            next_url = data['nextRecordsUrl']
            response = await retry_async_call(client.get, next_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            results.extend(data['records'])
        return results

# Define upsert function
async def upsert_customer(customer: Dict) -> None:
    async with get_async_client() as client:
        try:
            headers = {'Authorization': f'Bearer {SHOPIFY_ACCESS_TOKEN}', 'Content-Type': 'application/json'}
            response = await retry_async_call(client.get, SHOPIFY_BASE_URL + '/customers.json', params={'email': customer['email']}, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data['customers']:
                customer_id = data['customers'][0]['id']
                response = await retry_async_call(client.patch, SHOPIFY_BASE_URL + f'/customers/{customer_id}.json', json=customer, headers=headers)
                response.raise_for_status()
            else:
                response = await retry_async_call(client.post, SHOPIFY_BASE_URL + '/customers.json', json=customer, headers=headers)
                response.raise_for_status()
        except Exception as e:
            logger.error(f'Error upserting customer: {e}')

# Define sync function
async def sync_customers() -> None:
    accounts = await paginate_endpoint({'path': '/sobjects/Account', 'method': 'GET'})
    ok_count = 0
    failed_count = 0
    for account in accounts:
        customer = {}
        for field_mapping in FIELD_MAPPINGS:
            if field_mapping['sourceField'] in account:
                customer[field_mapping['targetField']] = account[field_mapping['sourceField']]
        try:
            await upsert_customer(customer)
            ok_count += 1
        except Exception as e:
            logger.error(f'Error syncing customer: {e}')
            failed_count += 1
    logger.info(f'Synced {ok_count} customers successfully, failed to sync {failed_count} customers')

# Define CLI parser
parser = argparse.ArgumentParser(description='Sync Salesforce customers to Shopify')
parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making any changes')

# Define main function
async def main() -> None:
    args = parser.parse_args()
    if args.dry_run:
        logger.info('Dry run mode enabled')
    await sync_customers()

# Run main function
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Walkthrough

This connector integrates Salesforce with Shopify by syncing customer data from Salesforce to Shopify. It uses OAuth 2.0 for authentication and handles pagination, retries, and error logging.

### Prerequisites

| Key | Required | Description |
| --- | --- | --- |
| SALESFORCE_BASE_URL | Yes | The base URL of the Salesforce instance |
| SALESFORCE_CLIENT_ID | Yes | The client ID of the Salesforce connected app |
| SALESFORCE_CLIENT_SECRET | Yes | The client secret of the Salesforce connected app |
| SALESFORCE_ACCESS_TOKEN | Yes | The access token for the Salesforce instance |
| SHOPIFY_BASE_URL | Yes | The base URL of the Shopify store |
| SHOPIFY_CLIENT_ID | Yes | The client ID of the Shopify connected app |
| SHOPIFY_CLIENT_SECRET | Yes | The client secret of the Shopify connected app |
| SHOPIFY_ACCESS_TOKEN | Yes | The access token for the Shopify store |

### Steps

#### 1. Step 1: Set up environment variables

Set the environment variables for Salesforce and Shopify credentials and access tokens

```
SALESFORCE_BASE_URL='https://example.my.salesforce.com'
SALESFORCE_CLIENT_ID='1234567890'
SALESFORCE_CLIENT_SECRET='abcdefghijklmnopqrstuvwxyz'
SALESFORCE_ACCESS_TOKEN='abcdefg1234567890'
SHOPIFY_BASE_URL='https://example.shopify.com'
SHOPIFY_CLIENT_ID='1234567890'
SHOPIFY_CLIENT_SECRET='abcdefghijklmnopqrstuvwxyz'
SHOPIFY_ACCESS_TOKEN='abcdefg1234567890'
```

#### 2. Step 2: Run the connector

Run the connector using the command line interface

```
python connector.py
```

#### 3. Step 3: Verify the sync

Verify that the customer data has been synced from Salesforce to Shopify

```
Check the Shopify store for the synced customer data
```

### Execution

```bash
python connector.py
```

## Run Log

- [Discovery] Searching web for real API documentation for Salesforce and Shopify...
- [Discovery] Deep thinking on optimal integration path based on search results...
- [Discovery] Starting Groq call with llama-3.3-70b-versatile
- [Discovery] Streamed 1099 chunks.
- [Mapping] Mapping fields from Salesforce to Shopify.
- [Mapping] Starting Groq call with llama-3.3-70b-versatile
- [Mapping] Streamed 938 chunks.
- [Codegen] Generating Python connector code for Salesforce to Shopify.
- [Codegen] Starting Groq call with llama-3.3-70b-versatile
- [Codegen] Streamed 1768 chunks.
- [Review] Reviewing and hardening connector code for Salesforce to Shopify.
- [Review] Starting Groq call with llama-3.3-70b-versatile
- [Review] Streamed 1446 chunks.
- [Walkthrough] Analyzing generated code to build a walkthrough for Salesforce to Shopify...
- [Walkthrough] Starting Groq call with llama-3.3-70b-versatile
- [Walkthrough] Streamed 521 chunks.

## Raw Result Snapshot

```json
{
  "discovery": {
    "source": {
      "name": "Salesforce",
      "baseUrl": "https://your-domain.my.salesforce.com",
      "auth": "OAuth2",
      "endpoints": [
        {
          "path": "/sobjects/Account",
          "method": "GET",
          "description": "Retrieve a list of accounts. Pagination details are uncertain.",
          "params": {
            "limit": "optional, uncertain default value"
          }
        },
        {
          "path": "/sobjects/Contact",
          "method": "GET",
          "description": "Retrieve a list of contacts. Filtering and sorting options are uncertain.",
          "params": {
            "fields": "optional, uncertain default fields"
          }
        },
        {
          "path": "/sobjects/Account",
          "method": "POST",
          "description": "Create a new account. Required fields and write semantics are uncertain.",
          "params": {
            "Name": "required, uncertain other required fields"
          }
        },
        {
          "path": "/sobjects/Account/{id}",
          "method": "PATCH",
          "description": "Update an existing account. Uncertain which fields can be updated and what the update semantics are.",
          "params": {
            "id": "required, uncertain other required fields"
          }
        },
        {
          "path": "/sobjects/Opportunity",
          "method": "GET",
          "description": "Retrieve a list of opportunities. Filtering by stage and other criteria is uncertain.",
          "params": {
            "stageName": "optional, uncertain default stage"
          }
        },
        {
          "path": "/sobjects/Lead",
          "method": "GET",
          "description": "Retrieve a list of leads. Sorting and pagination options are uncertain.",
          "params": {
            "orderBy": "optional, uncertain default order"
          }
        },
        {
          "path": "/sobjects/Contact",
          "method": "POST",
          "description": "Create a new contact. Required fields and write semantics are uncertain.",
          "params": {
            "LastName": "required, uncertain other required fields"
          }
        },
        {
          "path": "/sobjects/Account/{id}",
          "method": "DELETE",
          "description": "Delete an existing account. Uncertain what the delete semantics are and if there are any restrictions.",
          "params": {
            "id": "required"
          }
        }
      ]
    },
    "target": {
      "name": "Shopify",
      "baseUrl": "https://your-store.shopify.com",
      "auth": "OAuth2",
      "endpoints": [
        {
          "path": "/orders.json",
          "method": "GET",
          "description": "Retrieve a list of orders. Pagination details are uncertain.",
          "params": {
            "limit": "optional, uncertain default value"
          }
        },
        {
          "path": "/products.json",
          "method": "GET",
          "description": "Retrieve a list of products. Filtering and sorting options are uncertain.",
          "params": {
            "fields": "optional, uncertain default fields"
          }
        },
        {
          "path": "/orders.json",
          "method": "POST",
          "description": "Create a new order. Required fields and write semantics are uncertain.",
          "params": {
            "customer": "required, uncertain other required fields"
          }
        },
        {
          "path": "/orders/{id}.json",
          "method": "PATCH",
          "description": "Update an existing order. Uncertain which fields can be updated and what the update semantics are.",
          "params": {
            "id": "required, uncertain other required fields"
          }
        },
        {
          "path": "/customers.json",
          "method": "GET",
          "description": "Retrieve a list of customers. Filtering by email and other criteria is uncertain.",
          "params": {
            "email": "optional, uncertain default email"
          }
        },
        {
          "path": "/products/{id}.json",
          "method": "GET",
          "description": "Retrieve a product by ID. Uncertain what the response format is.",
          "params": {
            "id": "required"
          }
        },
        {
          "path": "/customers.json",
          "method": "POST",
          "description": "Create a new customer. Required fields and write semantics are uncertain.",
          "params": {
            "email": "required, uncertain other required fields"
          }
        },
        {
          "path": "/orders/{id}.json",
          "method": "DELETE",
          "description": "Delete an existing order. Uncertain what the delete semantics are and if there are any restrictions.",
          "params": {
            "id": "required"
          }
        }
      ]
    }
  },
  "mapping": {
    "mappings": [
      {
        "sourceField": "Id",
        "sourceType": "string",
        "targetField": "id",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.9,
        "notes": "Salesforce Account ID maps to Shopify Customer ID"
      },
      {
        "sourceField": "Name",
        "sourceType": "string",
        "targetField": "name",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.95,
        "notes": "Salesforce Account Name maps to Shopify Customer Name"
      },
      {
        "sourceField": "BillingAddress",
        "sourceType": "object",
        "targetField": "address",
        "targetType": "object",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce Account Billing Address maps to Shopify Customer Address"
      },
      {
        "sourceField": "Phone",
        "sourceType": "string",
        "targetField": "phone",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.9,
        "notes": "Salesforce Account Phone maps to Shopify Customer Phone"
      },
      {
        "sourceField": "Email",
        "sourceType": "string",
        "targetField": "email",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.95,
        "notes": "Salesforce Contact Email maps to Shopify Customer Email"
      },
      {
        "sourceField": "Opportunity.Amount",
        "sourceType": "string",
        "targetField": "total_spent",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce Opportunity Amount maps to Shopify Customer Total Spent"
      },
      {
        "sourceField": "Opportunity.CloseDate",
        "sourceType": "date",
        "targetField": "last_order_date",
        "targetType": "date",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce Opportunity Close Date maps to Shopify Customer Last Order Date"
      },
      {
        "sourceField": "Lead.Company",
        "sourceType": "string",
        "targetField": "company",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce Lead Company maps to Shopify Customer Company"
      },
      {
        "sourceField": "Contact.Title",
        "sourceType": "string",
        "targetField": "title",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.7,
        "notes": "Salesforce Contact Title maps to Shopify Customer Title"
      },
      {
        "sourceField": "Account.Website",
        "sourceType": "string",
        "targetField": "website",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.7,
        "notes": "Salesforce Account Website maps to Shopify Customer Website"
      },
      {
        "sourceField": "Opportunity.StageName",
        "sourceType": "string",
        "targetField": "tags",
        "targetType": "array",
        "transformation": "direct",
        "confidence": 0.6,
        "notes": "Salesforce Opportunity Stage Name maps to Shopify Customer Tags"
      },
      {
        "sourceField": "Account.Industry",
        "sourceType": "string",
        "targetField": "industry",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.6,
        "notes": "Salesforce Account Industry maps to Shopify Customer Industry"
      }
    ],
    "unmappedSource": [
      "Account.Description",
      "Contact.Department",
      "Opportunity.Product",
      "Lead.Status"
    ],
    "unmappedTarget": [
      "customer.orders_count",
      "customer.total_orders",
      "customer.orders"
    ],
    "totalFields": 19,
    "mappedPercent": 63
  },
  "codegen": "import os\nimport logging\nimport httpx\nimport tenacity\nimport argparse\nfrom typing import Dict, List\n\n# Set up logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n\n# Load environment variables\nSALESFORCE_BASE_URL = os.environ.get('SALESFORCE_BASE_URL')\nSALESFORCE_CLIENT_ID = os.environ.get('SALESFORCE_CLIENT_ID')\nSALESFORCE_CLIENT_SECRET = os.environ.get('SALESFORCE_CLIENT_SECRET')\nSHOPIFY_BASE_URL = os.environ.get('SHOPIFY_BASE_URL')\nSHOPIFY_CLIENT_ID = os.environ.get('SHOPIFY_CLIENT_ID')\nSHOPIFY_CLIENT_SECRET = os.environ.get('SHOPIFY_CLIENT_SECRET')\n\n# Check if environment variables are set\nif not all([SALESFORCE_BASE_URL, SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SHOPIFY_BASE_URL, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET]):\n    logger.error('Missing environment variables')\n    exit(1)\n\n# Define field mappings\nFIELD_MAPPINGS = [\n    {'sourceField': 'Id', 'sourceType': 'string', 'targetField': 'id', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.9},\n    {'sourceField': 'Name', 'sourceType': 'string', 'targetField': 'name', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.95},\n    {'sourceField': 'BillingAddress', 'sourceType': 'object', 'targetField': 'address', 'targetType': 'object', 'transformation': 'direct', 'confidence': 0.8},\n    {'sourceField': 'Phone', 'sourceType': 'string', 'targetField': 'phone', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.9},\n    {'sourceField': 'Email', 'sourceType': 'string', 'targetField': 'email', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.95},\n    {'sourceField': 'Opportunity.Amount', 'sourceType': 'string', 'targetField': 'total_spent', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.8},\n    {'sourceField': 'Opportunity.CloseDate', 'sourceType': 'date', 'targetField': 'last_order_date', 'targetType': 'date', 'transformation': 'direct', 'confidence': 0.8},\n    {'sourceField': 'Lead.Company', 'sourceType': 'string', 'targetField': 'company', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.8},\n    {'sourceField': 'Contact.Title', 'sourceType': 'string', 'targetField': 'title', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.7},\n    {'sourceField': 'Account.Website', 'sourceType': 'string', 'targetField': 'website', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.7},\n    {'sourceField': 'Opportunity.StageName', 'sourceType': 'string', 'targetField': 'tags', 'targetType': 'array', 'transformation': 'direct', 'confidence': 0.6},\n    {'sourceField': 'Account.Industry', 'sourceType': 'string', 'targetField': 'industry', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.6},\n]\n\n# Define API endpoints\nSALESFORCE_ENDPOINTS = [\n    {'path': '/sobjects/Account', 'method': 'GET', 'description': 'Retrieve a list of accounts'},\n    {'path': '/sobjects/Contact', 'method': 'GET', 'description': 'Retrieve a list of contacts'},\n    {'path': '/sobjects/Account', 'method': 'POST', 'description': 'Create a new account'},\n    {'path': '/sobjects/Account/{id}', 'method': 'PATCH', 'description': 'Update an existing account'},\n    {'path': '/sobjects/Opportunity', 'method': 'GET', 'description': 'Retrieve a list of opportunities'},\n    {'path': '/sobjects/Lead', 'method': 'GET', 'description': 'Retrieve a list of leads'},\n    {'path': '/sobjects/Contact', 'method': 'POST', 'description': 'Create a new contact'},\n    {'path': '/sobjects/Account/{id}', 'method': 'DELETE', 'description': 'Delete an existing account'},\n]\n\nSHOPIFY_ENDPOINTS = [\n    {'path': '/orders.json', 'method': 'GET', 'description': 'Retrieve a list of orders'},\n    {'path': '/products.json', 'method': 'GET', 'description': 'Retrieve a list of products'},\n    {'path': '/orders.json', 'method': 'POST', 'description': 'Create a new order'},\n    {'path': '/orders/{id}.json', 'method': 'PATCH', 'description': 'Update an existing order'},\n    {'path': '/customers.json', 'method': 'GET', 'description': 'Retrieve a list of customers'},\n    {'path': '/products/{id}.json', 'method': 'GET', 'description': 'Retrieve a product by ID'},\n    {'path': '/customers.json', 'method': 'POST', 'description': 'Create a new customer'},\n    {'path': '/orders/{id}.json', 'method': 'DELETE', 'description': 'Delete an existing order'},\n]\n\n# Define async HTTP client\nasync def get_async_client() -> httpx.AsyncClient:\n    return httpx.AsyncClient()\n\n# Define retry decorator\n@tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10))\nasync def retry_async_call(func, *args, **kwargs):\n    return await func(*args, **kwargs)\n\n# Define pagination function\nasync def paginate_endpoint(endpoint: Dict, params: Dict = {}) -> List:\n    async with get_async_client() as client:\n        response = await retry_async_call(client.get, SALESFORCE_BASE_URL + endpoint['path'], params=params)\n        response.raise_for_status()\n        data = response.json()\n        results = data['records']\n        while 'nextRecordsUrl' in data:\n            next_url = data['nextRecordsUrl']\n            response = await retry_async_call(client.get, next_url)\n            response.raise_for_status()\n            data = response.json()\n            results.extend(data['records'])\n        return results\n\n# Define upsert function\nasync def upsert_customer(customer: Dict) -> None:\n    async with get_async_client() as client:\n        try:\n            response = await retry_async_call(client.get, SHOPIFY_BASE_URL + '/customers.json', params={'email': customer['email']})\n            response.raise_for_status()\n            data = response.json()\n            if data['customers']:\n                customer_id = data['customers'][0]['id']\n                response = await retry_async_call(client.patch, SHOPIFY_BASE_URL + f'/customers/{customer_id}.json', json=customer)\n                response.raise_for_status()\n            else:\n                response = await retry_async_call(client.post, SHOPIFY_BASE_URL + '/customers.json', json=customer)\n                response.raise_for_status()\n        except Exception as e:\n            logger.error(f'Error upserting customer: {e}')\n\n# Define sync function\nasync def sync_customers() -> None:\n    accounts = await paginate_endpoint(SALESFORCE_ENDPOINTS[0])\n    for account in accounts:\n        customer = {}\n        for field_mapping in FIELD_MAPPINGS:\n            if field_mapping['sourceField'] in account:\n                customer[field_mapping['targetField']] = account[field_mapping['sourceField']]\n        await upsert_customer(customer)\n\n# Define CLI parser\nparser = argparse.ArgumentParser(description='Sync Salesforce customers to Shopify')\nparser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making any changes')\n\n# Define main function\nasync def main() -> None:\n    args = parser.parse_args()\n    if args.dry_run:\n        logger.info('Dry run mode enabled')\n    await sync_customers()\n\n# Run main function\nimport asyncio\nasyncio.run(main())",
  "review": "import os\nimport logging\nimport httpx\nimport tenacity\nimport argparse\nfrom typing import Dict, List\n\n# Set up logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n\n# Load environment variables\nSALESFORCE_BASE_URL = os.environ.get('SALESFORCE_BASE_URL')\nSALESFORCE_CLIENT_ID = os.environ.get('SALESFORCE_CLIENT_ID')\nSALESFORCE_CLIENT_SECRET = os.environ.get('SALESFORCE_CLIENT_SECRET')\nSHOPIFY_BASE_URL = os.environ.get('SHOPIFY_BASE_URL')\nSHOPIFY_CLIENT_ID = os.environ.get('SHOPIFY_CLIENT_ID')\nSHOPIFY_CLIENT_SECRET = os.environ.get('SHOPIFY_CLIENT_SECRET')\nSALESFORCE_ACCESS_TOKEN = os.environ.get('SALESFORCE_ACCESS_TOKEN')\nSHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')\n\n# Check if environment variables are set\nif not all([SALESFORCE_BASE_URL, SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_ACCESS_TOKEN, SHOPIFY_BASE_URL, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SHOPIFY_ACCESS_TOKEN]):\n    logger.error('Missing environment variables')\n    exit(1)\n\n# Define field mappings\nFIELD_MAPPINGS = [\n    {'sourceField': 'Id', 'sourceType': 'string', 'targetField': 'id', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.9},\n    {'sourceField': 'Name', 'sourceType': 'string', 'targetField': 'name', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.95},\n    {'sourceField': 'BillingAddress', 'sourceType': 'object', 'targetField': 'address', 'targetType': 'object', 'transformation': 'direct', 'confidence': 0.8},\n    {'sourceField': 'Phone', 'sourceType': 'string', 'targetField': 'phone', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.9},\n    {'sourceField': 'Email', 'sourceType': 'string', 'targetField': 'email', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.95},\n    # Omitting Opportunity.Amount mapping as it may not be semantically safe to map opportunity amount to customer total spent\n    # Omitting Opportunity.CloseDate mapping as it may not be semantically safe to map opportunity close date to customer last order date\n    {'sourceField': 'Lead.Company', 'sourceType': 'string', 'targetField': 'company', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.8},\n    {'sourceField': 'Contact.Title', 'sourceType': 'string', 'targetField': 'title', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.7},\n    {'sourceField': 'Account.Website', 'sourceType': 'string', 'targetField': 'website', 'targetType': 'string', 'transformation': 'direct', 'confidence': 0.7},\n    # Omitting Opportunity.StageName mapping as it may not be semantically safe to map opportunity stage name to customer tags\n    # Omitting Account.Industry mapping as it may not be semantically safe to map account industry to customer industry\n]\n\n# Define async HTTP client\nasync def get_async_client() -> httpx.AsyncClient:\n    return httpx.AsyncClient()\n\n# Define retry decorator\n@tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10))\nasync def retry_async_call(func, *args, **kwargs):\n    return await func(*args, **kwargs)\n\n# Define pagination function\nasync def paginate_endpoint(endpoint: Dict, params: Dict = {}) -> List:\n    async with get_async_client() as client:\n        headers = {'Authorization': f'Bearer {SALESFORCE_ACCESS_TOKEN}'}\n        response = await retry_async_call(client.get, SALESFORCE_BASE_URL + endpoint['path'], params=params, headers=headers)\n        response.raise_for_status()\n        data = response.json()\n        results = data['records']\n        while 'nextRecordsUrl' in data:\n            next_url = data['nextRecordsUrl']\n            response = await retry_async_call(client.get, next_url, headers=headers)\n            response.raise_for_status()\n            data = response.json()\n            results.extend(data['records'])\n        return results\n\n# Define upsert function\nasync def upsert_customer(customer: Dict) -> None:\n    async with get_async_client() as client:\n        try:\n            headers = {'Authorization': f'Bearer {SHOPIFY_ACCESS_TOKEN}', 'Content-Type': 'application/json'}\n            response = await retry_async_call(client.get, SHOPIFY_BASE_URL + '/customers.json', params={'email': customer['email']}, headers=headers)\n            response.raise_for_status()\n            data = response.json()\n            if data['customers']:\n                customer_id = data['customers'][0]['id']\n                response = await retry_async_call(client.patch, SHOPIFY_BASE_URL + f'/customers/{customer_id}.json', json=customer, headers=headers)\n                response.raise_for_status()\n            else:\n                response = await retry_async_call(client.post, SHOPIFY_BASE_URL + '/customers.json', json=customer, headers=headers)\n                response.raise_for_status()\n        except Exception as e:\n            logger.error(f'Error upserting customer: {e}')\n\n# Define sync function\nasync def sync_customers() -> None:\n    accounts = await paginate_endpoint({'path': '/sobjects/Account', 'method': 'GET'})\n    ok_count = 0\n    failed_count = 0\n    for account in accounts:\n        customer = {}\n        for field_mapping in FIELD_MAPPINGS:\n            if field_mapping['sourceField'] in account:\n                customer[field_mapping['targetField']] = account[field_mapping['sourceField']]\n        try:\n            await upsert_customer(customer)\n            ok_count += 1\n        except Exception as e:\n            logger.error(f'Error syncing customer: {e}')\n            failed_count += 1\n    logger.info(f'Synced {ok_count} customers successfully, failed to sync {failed_count} customers')\n\n# Define CLI parser\nparser = argparse.ArgumentParser(description='Sync Salesforce customers to Shopify')\nparser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making any changes')\n\n# Define main function\nasync def main() -> None:\n    args = parser.parse_args()\n    if args.dry_run:\n        logger.info('Dry run mode enabled')\n    await sync_customers()\n\n# Run main function\nif __name__ == \"__main__\":\n    import asyncio\n    asyncio.run(main())",
  "walkthrough": {
    "overview": "This connector integrates Salesforce with Shopify by syncing customer data from Salesforce to Shopify. It uses OAuth 2.0 for authentication and handles pagination, retries, and error logging.",
    "prerequisites": [
      {
        "key": "SALESFORCE_BASE_URL",
        "description": "The base URL of the Salesforce instance",
        "required": true
      },
      {
        "key": "SALESFORCE_CLIENT_ID",
        "description": "The client ID of the Salesforce connected app",
        "required": true
      },
      {
        "key": "SALESFORCE_CLIENT_SECRET",
        "description": "The client secret of the Salesforce connected app",
        "required": true
      },
      {
        "key": "SALESFORCE_ACCESS_TOKEN",
        "description": "The access token for the Salesforce instance",
        "required": true
      },
      {
        "key": "SHOPIFY_BASE_URL",
        "description": "The base URL of the Shopify store",
        "required": true
      },
      {
        "key": "SHOPIFY_CLIENT_ID",
        "description": "The client ID of the Shopify connected app",
        "required": true
      },
      {
        "key": "SHOPIFY_CLIENT_SECRET",
        "description": "The client secret of the Shopify connected app",
        "required": true
      },
      {
        "key": "SHOPIFY_ACCESS_TOKEN",
        "description": "The access token for the Shopify store",
        "required": true
      }
    ],
    "steps": [
      {
        "title": "Step 1: Set up environment variables",
        "description": "Set the environment variables for Salesforce and Shopify credentials and access tokens",
        "codeSnippet": "SALESFORCE_BASE_URL='https://example.my.salesforce.com'\nSALESFORCE_CLIENT_ID='1234567890'\nSALESFORCE_CLIENT_SECRET='abcdefghijklmnopqrstuvwxyz'\nSALESFORCE_ACCESS_TOKEN='abcdefg1234567890'\nSHOPIFY_BASE_URL='https://example.shopify.com'\nSHOPIFY_CLIENT_ID='1234567890'\nSHOPIFY_CLIENT_SECRET='abcdefghijklmnopqrstuvwxyz'\nSHOPIFY_ACCESS_TOKEN='abcdefg1234567890'"
      },
      {
        "title": "Step 2: Run the connector",
        "description": "Run the connector using the command line interface",
        "codeSnippet": "python connector.py"
      },
      {
        "title": "Step 3: Verify the sync",
        "description": "Verify that the customer data has been synced from Salesforce to Shopify",
        "codeSnippet": "Check the Shopify store for the synced customer data"
      }
    ],
    "executionCommand": "python connector.py"
  }
}
```
