from azure.mgmt.compute.models import DiskCreateOption
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.identity import AzureCliCredential
import os


## Documentation
# https://docs.microsoft.com/en-us/azure/developer/python/azure-sdk-library-usage-patterns#asynchronous-operations
# https://docs.microsoft.com/fr-fr/python/api/?view=azure-python



# Acquire a credential object using CLI-based authentication.
credential = AzureCliCredential()

# Retrieve subscription ID from environment variable.
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

# Obtain the management object for resources.
resource_client = ResourceManagementClient(credential, subscription_id)


MAIN_REGION="westeurope"
DR_REGION="northeurope"
BLOB_ENDPOINT="https://jnowalczyk.blob.core.windows.net/"


# Provision the resource group.
rg_result = resource_client.resource_groups.create_or_update(
    "jnowalczyk-rg",
    {
        "location": MAIN_REGION
    }
)

print(f"Provisioned resource group {rg_result.name} in the {rg_result.location} region")

compute_client = ComputeManagementClient(credential, subscription_id)

# Create disk
poller = compute_client.disks.begin_create_or_update(
    'jnowalczyk-rg',
    'jnowalczyk-disk',
    {
        'location': MAIN_REGION,
        'disk_size_gb': 1,
        'creation_data': {
            'create_option': DiskCreateOption.empty
        }
    }
)
disk_resource = poller.result()

print(f"Provisioned disk {disk_resource.name} in the {disk_resource.location} region")

managed_disk = compute_client.disks.get(rg_result.name, disk_resource.name)

#Create snapshot in the MAIN region
async_snapshot_creation = compute_client.snapshots.begin_create_or_update(
        rg_result.name,
        'jnowalczyk_disk_snapshot',
        {
            'location': MAIN_REGION,
            'creation_data': {
                'create_option': 'Copy',
                'source_uri': managed_disk.id
            }
        }
    )
snapshot = async_snapshot_creation.result()

# Grant snapshot access to get sas url
async_snapshot_grant_access = compute_client.snapshots.begin_grant_access(
        rg_result.name,
        'jnowalczyk_disk_snapshot',
        {
            'access': 'Read',
            'duration_in_seconds': 7200  
        }
    )

snapshot_sas = async_snapshot_grant_access.result()

