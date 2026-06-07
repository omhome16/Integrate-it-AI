"""
Production Salesforce to Shopify connector.

This file syncs Salesforce Accounts and Contacts into Shopify Customers, and
Salesforce Product2 records plus standard PricebookEntry prices into Shopify
Products. It intentionally does not sync Salesforce Opportunities to Shopify
Orders because an opportunity is a potential sale while a Shopify order is a
completed purchase that requires customer, payment, and line-item semantics.

Required environment variables:
  SALESFORCE_BASE_URL: Salesforce instance URL, such as https://example.my.salesforce.com
  SALESFORCE_CLIENT_ID: Salesforce connected app client ID
  SALESFORCE_CLIENT_SECRET: Salesforce connected app client secret
  SHOPIFY_STORE_URL: Shopify store URL, such as https://example.myshopify.com
  SHOPIFY_ACCESS_TOKEN: Shopify Admin API access token

Optional behavior:
  Run with --dry-run to fetch and transform data without writing to Shopify.
  Run with --reset to clear the local checkpoint and re-run all sync steps.
"""

# -- 1. IMPORTS -------------------------------------------------------------
import os
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


# -- 2. LOGGING SETUP -------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# -- 3. CONFIG DATACLASSES --------------------------------------------------
@dataclass
class SalesforceConfig:
    """Required Salesforce API configuration loaded eagerly from env vars."""

    # FIX 12: os.environ fails fast when required configuration is missing.
    base_url: str = field(default_factory=lambda: os.environ["SALESFORCE_BASE_URL"])
    client_id: str = field(default_factory=lambda: os.environ["SALESFORCE_CLIENT_ID"])
    client_secret: str = field(default_factory=lambda: os.environ["SALESFORCE_CLIENT_SECRET"])
    api_version: str = "v52.0"

    def normalized_base_url(self) -> str:
        """Return the Salesforce base URL without a trailing slash."""

        return self.base_url.rstrip("/")


@dataclass
class ShopifyConfig:
    """Required Shopify Admin API configuration loaded eagerly from env vars."""

    # FIX 1 and FIX 12: SHOPIFY_ACCESS_TOKEN replaces unclear API password naming.
    store_url: str = field(default_factory=lambda: os.environ["SHOPIFY_STORE_URL"])
    access_token: str = field(default_factory=lambda: os.environ["SHOPIFY_ACCESS_TOKEN"])
    api_version: str = "2022-07"

    @property
    def base_url(self) -> str:
        """Return the Shopify Admin API base URL."""

        return f"{self.store_url.rstrip('/')}/admin/api/{self.api_version}"


# -- 4. AUTHENTICATION ------------------------------------------------------
def salesforce_headers(token: str) -> Dict[str, str]:
    """Build Salesforce authorization headers from an OAuth access token."""

    # FIX 1: OAuth access token is used as Bearer token, never client_id.
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def shopify_headers(access_token: str) -> Dict[str, str]:
    """Build Shopify Admin API headers."""

    # FIX 1: Shopify Admin API uses X-Shopify-Access-Token.
    return {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}


async def get_salesforce_token(client: httpx.AsyncClient, config: SalesforceConfig) -> str:
    """Exchange Salesforce client credentials for an OAuth2 access token."""

    # FIX 1: client_id and client_secret must be exchanged at /services/oauth2/token.
    response = await client.post(
        f"{config.normalized_base_url()}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        },
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise ValueError("Salesforce token response did not include access_token")
    return str(token)


# -- 5. RATE LIMITER --------------------------------------------------------
class LeakyBucketLimiter:
    """Minimal async leaky-bucket limiter for serial API calls."""

    # FIX 7: Shopify allows roughly 40 requests per 20 seconds.
    def __init__(self, rate_per_second: float) -> None:
        if rate_per_second <= 0:
            raise ValueError("rate_per_second must be positive")
        self._interval = 1.0 / rate_per_second
        self._last = 0.0

    async def wait(self) -> None:
        """Wait until the next request can be sent."""

        now = time.monotonic()
        delta = self._interval - (now - self._last)
        if delta > 0:
            await asyncio.sleep(delta)
        self._last = time.monotonic()


shopify_limiter = LeakyBucketLimiter(rate_per_second=2.0)


# -- 6. HTTP REQUEST HELPER -------------------------------------------------
@retry(
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    limiter: Optional[LeakyBucketLimiter] = None,
) -> httpx.Response:
    """Send an HTTP request with retries, safe defaults, and optional limiting."""

    # FIX 7: every Shopify request passes the limiter before the HTTP call.
    if limiter:
        await limiter.wait()

    # FIX 4 and FIX 9: body maps to httpx json= and defaults are never mutable.
    response = await client.request(
        method,
        url,
        headers=headers or {},
        params=params,
        json=body,
    )
    response.raise_for_status()
    return response


# -- 7. PAGINATION HELPERS --------------------------------------------------
async def soql_query_all(
    client: httpx.AsyncClient,
    config: SalesforceConfig,
    token: str,
    soql: str,
) -> List[Dict[str, Any]]:
    """Run a SOQL query and follow Salesforce nextRecordsUrl pages."""

    # FIX 2: Salesforce record reads use /query/ with SOQL, not object describe URLs.
    url: Optional[str] = (
        f"{config.normalized_base_url()}/services/data/{config.api_version}/query/"
    )
    params: Optional[Dict[str, Any]] = {"q": soql}
    records: List[Dict[str, Any]] = []

    # FIX 3: Salesforce pagination continues until done is true.
    while url:
        response = await request(
            client,
            "GET",
            url,
            headers=salesforce_headers(token),
            params=params,
        )
        payload = response.json()
        records.extend(payload.get("records", []))
        if payload.get("done", True):
            break
        next_url = payload.get("nextRecordsUrl")
        if not next_url:
            break
        url = f"{config.normalized_base_url()}{next_url}"
        params = None

    return records


async def shopify_list_all(
    client: httpx.AsyncClient,
    config: ShopifyConfig,
    endpoint: str,
    resource_key: str,
) -> List[Dict[str, Any]]:
    """List all Shopify records for an endpoint by following Link rel=next."""

    url: Optional[str] = f"{config.base_url}/{endpoint.lstrip('/')}"
    params: Optional[Dict[str, Any]] = {"limit": 250}
    records: List[Dict[str, Any]] = []

    # FIX 3: Shopify pagination is Link-header based.
    while url:
        response = await request(
            client,
            "GET",
            url,
            headers=shopify_headers(config.access_token),
            params=params,
            limiter=shopify_limiter,
        )
        records.extend(response.json().get(resource_key, []))
        url = parse_shopify_next_link(response.headers.get("Link", ""))
        params = None

    return records


def parse_shopify_next_link(link_header: str) -> Optional[str]:
    """Extract the next-page URL from a Shopify Link header."""

    # FIX 3: Link header parts contain rel="next" when another page exists.
    for part in link_header.split(","):
        if 'rel="next"' in part:
            return part.strip().split(";")[0].strip().strip("<>")
    return None


# -- 8. FIELD TRANSFORMATION FUNCTIONS -------------------------------------
def transform_billing_address(sf_account: Dict[str, Any]) -> Dict[str, str]:
    """Convert Salesforce billing fields into Shopify address fields."""

    # FIX 5: Salesforce flat billing fields map to Shopify address object fields.
    return {
        "address1": str(sf_account.get("BillingStreet") or ""),
        "city": str(sf_account.get("BillingCity") or ""),
        "province": str(sf_account.get("BillingState") or ""),
        "zip": str(sf_account.get("BillingPostalCode") or ""),
        "country": str(sf_account.get("BillingCountry") or ""),
    }


def split_full_name(full_name: str) -> Tuple[str, str]:
    """Split a full name into Shopify first_name and last_name fields."""

    # FIX 6: Shopify stores first_name and last_name separately.
    parts = (full_name or "").strip().split(" ", 1)
    if not parts or not parts[0]:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def map_account_contact_to_customer(
    account: Dict[str, Any],
    contact: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Map a Salesforce Account plus its first Contact to a Shopify Customer."""

    # FIX 15: Direct O(1) mapping replaces field mapping loops and if/elif chains.
    contact_data = contact or {}
    first_name, last_name = split_full_name(str(account.get("Name") or ""))
    customer: Dict[str, Any] = {
        "first_name": first_name,
        "last_name": last_name,
        "email": contact_data.get("Email") or "",
        "phone": contact_data.get("Phone") or "",
        "tags": f"sf_account_id:{account.get('Id')}",
        "addresses": [transform_billing_address(account)],
    }

    return remove_empty_values(customer)


def map_product_to_shopify(
    sf_product: Dict[str, Any],
    unit_price: Optional[Any],
) -> Dict[str, Any]:
    """Map a Salesforce Product2 record and price to a Shopify Product."""

    # FIX 15: Product mapping is explicit and constant-time.
    product_id = str(sf_product.get("Id") or "")
    price = "" if unit_price is None else str(unit_price)
    product: Dict[str, Any] = {
        "title": sf_product.get("Name") or "Untitled Salesforce Product",
        "body_html": sf_product.get("Description") or "",
        "product_type": sf_product.get("Family") or "",
        "tags": f"sf_product_id:{product_id}",
        "variants": [
            {
                "price": price,
                "sku": sf_product.get("ProductCode") or product_id,
            }
        ],
    }

    return remove_empty_values(product)


def remove_empty_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy without empty scalar values."""

    cleaned: Dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        if isinstance(value, list):
            cleaned[key] = value
            continue
        cleaned[key] = value
    return cleaned


def build_contact_map(contacts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map AccountId to the first Salesforce Contact found for that account."""

    # FIX 6: Email and phone come from Contact records linked by AccountId.
    contact_map: Dict[str, Dict[str, Any]] = {}
    for contact in contacts:
        account_id = contact.get("AccountId")
        if account_id and account_id not in contact_map:
            contact_map[str(account_id)] = contact
    return contact_map


def build_price_map(pricebook_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Map Salesforce Product2Id to standard PricebookEntry UnitPrice."""

    price_map: Dict[str, Any] = {}
    for entry in pricebook_entries:
        product_id = entry.get("Product2Id")
        if product_id and product_id not in price_map:
            price_map[str(product_id)] = entry.get("UnitPrice")
    return price_map


# -- 9. UPSERT FUNCTIONS ----------------------------------------------------
async def upsert_shopify_customer(
    client: httpx.AsyncClient,
    config: ShopifyConfig,
    customer: Dict[str, Any],
) -> Dict[str, Any]:
    """Update a Shopify customer by email when present, otherwise create it."""

    # FIX 4: Upsert customers by searching Shopify for the customer email first.
    headers = shopify_headers(config.access_token)
    email = customer.get("email")
    if email:
        search_response = await request(
            client,
            "GET",
            f"{config.base_url}/customers/search.json",
            headers=headers,
            params={"query": f"email:{email}"},
            limiter=shopify_limiter,
        )
        existing = search_response.json().get("customers", [])
        if existing:
            customer_id = existing[0]["id"]
            update_response = await request(
                client,
                "PUT",
                f"{config.base_url}/customers/{customer_id}.json",
                headers=headers,
                body={"customer": customer},
                limiter=shopify_limiter,
            )
            return update_response.json()["customer"]

    create_response = await request(
        client,
        "POST",
        f"{config.base_url}/customers.json",
        headers=headers,
        body={"customer": customer},
        limiter=shopify_limiter,
    )
    return create_response.json()["customer"]


async def upsert_shopify_product(
    client: httpx.AsyncClient,
    config: ShopifyConfig,
    product: Dict[str, Any],
    sf_product_id: str,
) -> Dict[str, Any]:
    """Update a Shopify product by Salesforce tag when present, otherwise create it."""

    # FIX 4: Store and search by sf_product_id tag to avoid duplicate products.
    headers = shopify_headers(config.access_token)
    tag = f"sf_product_id:{sf_product_id}"
    product["tags"] = tag

    search_response = await request(
        client,
        "GET",
        f"{config.base_url}/products.json",
        headers=headers,
        params={"tag": tag, "limit": 1},
        limiter=shopify_limiter,
    )
    existing = search_response.json().get("products", [])
    if existing:
        product_id = existing[0]["id"]
        update_response = await request(
            client,
            "PUT",
            f"{config.base_url}/products/{product_id}.json",
            headers=headers,
            body={"product": product},
            limiter=shopify_limiter,
        )
        return update_response.json()["product"]

    create_response = await request(
        client,
        "POST",
        f"{config.base_url}/products.json",
        headers=headers,
        body={"product": product},
        limiter=shopify_limiter,
    )
    return create_response.json()["product"]


# -- 10. SYNC FUNCTIONS -----------------------------------------------------
async def sync_customers(
    client: httpx.AsyncClient,
    sf_config: SalesforceConfig,
    shopify_config: ShopifyConfig,
    token: str,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """Sync Salesforce Accounts and Contacts into Shopify Customers."""

    # FIX 2: Account data is fetched with SOQL through the query endpoint.
    accounts = await soql_query_all(
        client,
        sf_config,
        token,
        (
            "SELECT Id, Name, BillingStreet, BillingCity, BillingState, "
            "BillingPostalCode, BillingCountry FROM Account"
        ),
    )
    contacts = await soql_query_all(
        client,
        sf_config,
        token,
        "SELECT Id, AccountId, Email, Phone FROM Contact",
    )
    contact_map = build_contact_map(contacts)
    ok = 0
    failed = 0

    # FIX 10: Each record is isolated so one bad account does not stop the sync.
    for account in accounts:
        account_id = str(account.get("Id") or "")
        try:
            customer_data = map_account_contact_to_customer(
                account,
                contact_map.get(account_id),
            )
            if dry_run:
                logger.info("[DRY RUN] Would upsert customer: %s", customer_data.get("email"))
            else:
                result = await upsert_shopify_customer(
                    client,
                    shopify_config,
                    customer_data,
                )
                logger.info("Upserted Shopify customer: %s", result.get("id"))
            ok += 1
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed customer for Account %s: %s %s",
                account_id,
                exc.response.status_code,
                exc.response.text,
            )
            failed += 1
        except Exception as exc:
            logger.error("Unexpected error for Account %s: %s", account_id, exc)
            failed += 1

    logger.info("Customers sync complete - OK: %s, Failed: %s", ok, failed)
    return ok, failed


async def sync_products(
    client: httpx.AsyncClient,
    sf_config: SalesforceConfig,
    shopify_config: ShopifyConfig,
    token: str,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """Sync Salesforce Product2 records into Shopify Products."""

    # FIX 2: Products and prices use SOQL queries, including standard pricebook.
    products = await soql_query_all(
        client,
        sf_config,
        token,
        "SELECT Id, Name, Description, ProductCode, Family FROM Product2 WHERE IsActive = true",
    )
    pricebook_entries = await soql_query_all(
        client,
        sf_config,
        token,
        "SELECT Product2Id, UnitPrice FROM PricebookEntry WHERE Pricebook2.IsStandard = true",
    )
    price_map = build_price_map(pricebook_entries)
    ok = 0
    failed = 0

    # FIX 10: Product failures are counted and logged per record.
    for product in products:
        product_id = str(product.get("Id") or "")
        try:
            product_data = map_product_to_shopify(product, price_map.get(product_id))
            if dry_run:
                logger.info("[DRY RUN] Would upsert product: %s", product_data.get("title"))
            else:
                result = await upsert_shopify_product(
                    client,
                    shopify_config,
                    product_data,
                    product_id,
                )
                logger.info("Upserted Shopify product: %s", result.get("id"))
            ok += 1
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed product for Product2 %s: %s %s",
                product_id,
                exc.response.status_code,
                exc.response.text,
            )
            failed += 1
        except Exception as exc:
            logger.error("Unexpected error for Product2 %s: %s", product_id, exc)
            failed += 1

    logger.info("Products sync complete - OK: %s, Failed: %s", ok, failed)
    return ok, failed


# FIX 8: Salesforce Opportunity to Shopify Order is not a direct mapping.
# Opportunity means potential sale in a pipeline. Order means completed purchase.
# Correct order sync would need Closed Won filtering, line items, variant IDs,
# customer matching, and financial status mapping in a custom implementation.


# -- 11. CHECKPOINT MANAGER -------------------------------------------------
class Checkpoint:
    """Persist completed sync steps so interrupted runs can resume."""

    # FIX 13: Completed top-level sync steps are stored in a local JSON file.
    def __init__(self, path: str = "sync_checkpoint.json") -> None:
        self._path = path
        self._data = self._load()

    def _load(self) -> Dict[str, str]:
        """Load checkpoint JSON, returning an empty state when absent or invalid."""

        try:
            with open(self._path, "r", encoding="utf-8") as checkpoint_file:
                loaded = json.load(checkpoint_file)
                if isinstance(loaded, dict):
                    return {str(key): str(value) for key, value in loaded.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        return {}

    def mark_done(self, step: str) -> None:
        """Mark a sync step as complete and persist the checkpoint."""

        self._data[step] = "done"
        with open(self._path, "w", encoding="utf-8") as checkpoint_file:
            json.dump(self._data, checkpoint_file, indent=2)

    def is_done(self, step: str) -> bool:
        """Return whether a sync step has already completed."""

        return self._data.get(step) == "done"

    def reset(self) -> None:
        """Clear checkpoint state and remove the checkpoint file if present."""

        self._data = {}
        try:
            os.remove(self._path)
        except FileNotFoundError:
            pass


# -- 12. MAIN ENTRY POINT ---------------------------------------------------
async def main(dry_run: bool = False, reset_checkpoint: bool = False) -> None:
    """Run the Salesforce to Shopify sync."""

    # FIX 12: Configuration is explicit and testable, not module global strings.
    sf_config = SalesforceConfig()
    shopify_config = ShopifyConfig()
    checkpoint = Checkpoint()

    # FIX 14: --reset clears completed step state for a full re-run.
    if reset_checkpoint:
        checkpoint.reset()
        logger.info("Checkpoint reset complete.")

    # FIX 14: --dry-run disables Shopify writes while keeping fetch and mapping.
    if dry_run:
        logger.info("DRY RUN - Shopify writes are disabled.")

    # FIX 11: Use one real AsyncClient context manager and pass it through.
    async with httpx.AsyncClient(timeout=30.0) as client:
        token = await get_salesforce_token(client, sf_config)

        if checkpoint.is_done("customers") and not dry_run:
            logger.info("Skipping customers sync; checkpoint already completed.")
        else:
            await sync_customers(client, sf_config, shopify_config, token, dry_run=dry_run)
            if not dry_run:
                checkpoint.mark_done("customers")

        if checkpoint.is_done("products") and not dry_run:
            logger.info("Skipping products sync; checkpoint already completed.")
        else:
            await sync_products(client, sf_config, shopify_config, token, dry_run=dry_run)
            if not dry_run:
                checkpoint.mark_done("products")


if __name__ == "__main__":
    # FIX 14: CLI flags allow safe dry runs and checkpoint reset.
    import argparse

    parser = argparse.ArgumentParser(description="Salesforce to Shopify connector")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch data but skip all Shopify writes",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear checkpoint and re-run all steps",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, reset_checkpoint=args.reset))
