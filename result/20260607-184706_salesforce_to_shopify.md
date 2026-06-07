# Integration Report: Salesforce to Shopify

- Generated: 2026-06-07T18:47:06+00:00
- Status: failed
- Source: Salesforce
- Target: Shopify
- Prompt: Connect Salesforce with Shopify

## Run Error

Client error '429 Too Many Requests' for url 'https://api.groq.com/openai/v1/chat/completions'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429

## API Discovery

### Source API: Salesforce

- Base URL: https://your-domain.my.salesforce.com
- Authentication: OAuth2

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /services/data/vXX.0/query/ | Retrieve records using SOQL (Salesforce Object Query Language), exact endpoint and parameters are uncertain |
| GET | /services/data/vXX.0/sobjects/ | Retrieve a list of available objects, exact endpoint and parameters are uncertain |
| GET | /services/data/vXX.0/sobjects/{objectName}/{id} | Retrieve a single record by ID, exact endpoint and parameters are uncertain |
| POST | /services/data/vXX.0/sobjects/{objectName} | Create a new record, exact endpoint and parameters are uncertain |
| PATCH | /services/data/vXX.0/sobjects/{objectName}/{id} | Update an existing record, exact endpoint and parameters are uncertain |
| DELETE | /services/data/vXX.0/sobjects/{objectName}/{id} | Delete a record, exact endpoint and parameters are uncertain |
| GET | /services/data/vXX.0/limits | Retrieve organization limits, exact endpoint and parameters are uncertain |

### Target API: Shopify

- Base URL: https://{shop}.shopify.com/admin/api/2022-04
- Authentication: OAuth2

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /products.json | Retrieve a list of products, exact endpoint and parameters are uncertain |
| GET | /orders.json | Retrieve a list of orders, exact endpoint and parameters are uncertain |
| GET | /customers.json | Retrieve a list of customers, exact endpoint and parameters are uncertain |
| POST | /products.json | Create a new product, exact endpoint and parameters are uncertain |
| PUT | /products/{productId}.json | Update an existing product, exact endpoint and parameters are uncertain |
| DELETE | /products/{productId}.json | Delete a product, exact endpoint and parameters are uncertain |
| GET | /webhooks.json | Retrieve a list of webhooks, exact endpoint and parameters are uncertain |

## Field Mapping

- Mapped fields: 12
- Total fields: 16
- Mapped percent: 75%

| Source Field | Target Field | Transformation | Confidence | Notes |
| --- | --- | --- | --- | --- |
| Id | id | direct | 90% | Salesforce object ID maps to Shopify product ID |
| Name | title | direct | 90% | Salesforce object name maps to Shopify product title |
| Description | body_html | direct | 80% | Salesforce object description maps to Shopify product description |
| PricebookEntry.UnitPrice | price | direct | 80% | Salesforce pricebook entry unit price maps to Shopify product price |
| Product2.Family | product_type | direct | 80% | Salesforce product family maps to Shopify product type |
| Account.Name | customer.name | direct | 80% | Salesforce account name maps to Shopify customer name |
| Contact.Email | customer.email | direct | 80% | Salesforce contact email maps to Shopify customer email |
| Order.TotalAmount | total_price | direct | 80% | Salesforce order total amount maps to Shopify order total price |
| Order.Status | financial_status | direct | 70% | Salesforce order status maps to Shopify order financial status |
| Opportunity.CloseDate | closed_at | direct | 70% | Salesforce opportunity close date maps to Shopify order closed at date |
| Product2.ImageUrl | image.src | direct | 70% | Salesforce product image URL maps to Shopify product image source |
| OrderItem.Quantity | quantity | direct | 70% | Salesforce order item quantity maps to Shopify order item quantity |

### Unmapped Source Fields

- Salesforce object created date
- Salesforce object last modified date

### Unmapped Target Fields

- Shopify product vendor
- Shopify order shipping address

## Reviewed Connector Code

No connector code was returned.

## Walkthrough

No walkthrough overview was returned.

### Prerequisites

| Key | Required | Description |
| --- | --- | --- |
| None | No | No prerequisites were returned. |

### Steps

No walkthrough steps were returned.

## Run Log

- [Discovery] Searching web for real API documentation for Salesforce and Shopify...
- [Discovery] Deep thinking on optimal integration path based on search results...
- [Discovery] Starting Groq call with llama-3.3-70b-versatile
- [Discovery] Streamed 931 chunks.
- [Mapping] Mapping fields from Salesforce to Shopify.
- [Mapping] Starting Groq call with llama-3.3-70b-versatile
- [Mapping] Streamed 978 chunks.
- [Codegen] Generating Python connector code for Salesforce to Shopify.
- [Codegen] Starting Groq call with llama-3.3-70b-versatile

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
          "path": "/services/data/vXX.0/query/",
          "method": "GET",
          "description": "Retrieve records using SOQL (Salesforce Object Query Language), exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/services/data/vXX.0/sobjects/",
          "method": "GET",
          "description": "Retrieve a list of available objects, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/services/data/vXX.0/sobjects/{objectName}/{id}",
          "method": "GET",
          "description": "Retrieve a single record by ID, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/services/data/vXX.0/sobjects/{objectName}",
          "method": "POST",
          "description": "Create a new record, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/services/data/vXX.0/sobjects/{objectName}/{id}",
          "method": "PATCH",
          "description": "Update an existing record, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/services/data/vXX.0/sobjects/{objectName}/{id}",
          "method": "DELETE",
          "description": "Delete a record, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/services/data/vXX.0/limits",
          "method": "GET",
          "description": "Retrieve organization limits, exact endpoint and parameters are uncertain",
          "params": {}
        }
      ]
    },
    "target": {
      "name": "Shopify",
      "baseUrl": "https://{shop}.shopify.com/admin/api/2022-04",
      "auth": "OAuth2",
      "endpoints": [
        {
          "path": "/products.json",
          "method": "GET",
          "description": "Retrieve a list of products, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/orders.json",
          "method": "GET",
          "description": "Retrieve a list of orders, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/customers.json",
          "method": "GET",
          "description": "Retrieve a list of customers, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/products.json",
          "method": "POST",
          "description": "Create a new product, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/products/{productId}.json",
          "method": "PUT",
          "description": "Update an existing product, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/products/{productId}.json",
          "method": "DELETE",
          "description": "Delete a product, exact endpoint and parameters are uncertain",
          "params": {}
        },
        {
          "path": "/webhooks.json",
          "method": "GET",
          "description": "Retrieve a list of webhooks, exact endpoint and parameters are uncertain",
          "params": {}
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
        "notes": "Salesforce object ID maps to Shopify product ID"
      },
      {
        "sourceField": "Name",
        "sourceType": "string",
        "targetField": "title",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.9,
        "notes": "Salesforce object name maps to Shopify product title"
      },
      {
        "sourceField": "Description",
        "sourceType": "string",
        "targetField": "body_html",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce object description maps to Shopify product description"
      },
      {
        "sourceField": "PricebookEntry.UnitPrice",
        "sourceType": "string",
        "targetField": "price",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce pricebook entry unit price maps to Shopify product price"
      },
      {
        "sourceField": "Product2.Family",
        "sourceType": "string",
        "targetField": "product_type",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce product family maps to Shopify product type"
      },
      {
        "sourceField": "Account.Name",
        "sourceType": "string",
        "targetField": "customer.name",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce account name maps to Shopify customer name"
      },
      {
        "sourceField": "Contact.Email",
        "sourceType": "string",
        "targetField": "customer.email",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce contact email maps to Shopify customer email"
      },
      {
        "sourceField": "Order.TotalAmount",
        "sourceType": "string",
        "targetField": "total_price",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.8,
        "notes": "Salesforce order total amount maps to Shopify order total price"
      },
      {
        "sourceField": "Order.Status",
        "sourceType": "string",
        "targetField": "financial_status",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.7,
        "notes": "Salesforce order status maps to Shopify order financial status"
      },
      {
        "sourceField": "Opportunity.CloseDate",
        "sourceType": "date",
        "targetField": "closed_at",
        "targetType": "date",
        "transformation": "direct",
        "confidence": 0.7,
        "notes": "Salesforce opportunity close date maps to Shopify order closed at date"
      },
      {
        "sourceField": "Product2.ImageUrl",
        "sourceType": "string",
        "targetField": "image.src",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.7,
        "notes": "Salesforce product image URL maps to Shopify product image source"
      },
      {
        "sourceField": "OrderItem.Quantity",
        "sourceType": "string",
        "targetField": "quantity",
        "targetType": "string",
        "transformation": "direct",
        "confidence": 0.7,
        "notes": "Salesforce order item quantity maps to Shopify order item quantity"
      }
    ],
    "unmappedSource": [
      "Salesforce object created date",
      "Salesforce object last modified date"
    ],
    "unmappedTarget": [
      "Shopify product vendor",
      "Shopify order shipping address"
    ],
    "totalFields": 16,
    "mappedPercent": 75
  }
}
```
