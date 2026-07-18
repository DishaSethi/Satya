import os
import uuid
from azure.storage.blob.aio import BlobServiceClient

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

async def upload_image_to_azure(file_bytes: bytes, filename: str) -> str:
    """Uploads raw bytes to Azure Blob Storage and returns the public URL."""
    # 1. Ensure a unique filename so we don't accidentally overwrite images
    unique_blob_name = f"{uuid.uuid4().hex[:8]}-{filename}"

    # 2. Connect to Azure
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

    async with blob_service_client:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(unique_blob_name)

        # 3. Upload the file
        await blob_client.upload_blob(file_bytes, overwrite=True)

    # 4. Construct and return the public URL for the React frontend
    account_name = AZURE_STORAGE_CONNECTION_STRING.split("AccountName=")[1].split(";")[0]
    public_url = f"https://{account_name}.blob.core.windows.net/{CONTAINER_NAME}/{unique_blob_name}"

    return public_url