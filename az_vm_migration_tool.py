#!/usr/bin/python
# Author: Umesh Panwar
# Date: June 20, 2024
# Description: This script will help you migrate VMs from one zone to another. It will take the VM details from a csv file and create snapshots, disks and VMs in the zone of your choice. 

# import the required libraries

import json
import subprocess
import logging
import csv
import sys


# Check if the csv file is passed as an argument
if len(sys.argv) < 2:
    print('Please pass the csv file as an argument')
    sys.exit(1)

# Existing Virtual Network Name, Subnet Name and Resource Group Name where the Virtual Network exists.
## Please provide the existing VNET name, Subnet name and Resource Group name where the VNET exists.
vnet_name = "<VNET Name>"
subnet_name = "<Subnet Name>"
vnet_rg = "<RG name where VNET exists>"

# Capture the subnet ID that is going to use in VM creation.
def capture_subnet_id():
    cmd = f"az network vnet subnet show --resource-group {vnet_rg} --vnet-name {vnet_name} --name {subnet_name}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error("Error getting subnet details: " + result.stderr.decode('utf-8'))
        raise Exception("Error capturing subnet ID")
    logging.info("Subnet details captured successfully.")
    subnet_id = json.loads(result.stdout.decode('utf-8'))
    logging.info(f"Subnet ID: {subnet_id['id']}")
    return subnet_id['id']


# Function to create snapshot of a data disk in Azure. To create a snapshot, it is recommended to have VM in stopped (deallocated) state. 
def create_snapshots():
    # Get the VM details
    cmd = f"az vm show --resource-group {resource_group} --name {vm_name}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error("Error getting VM details: " + result.stderr.decode('utf-8'))
        raise Exception("Error getting VM details")
    vm_details = json.loads(result.stdout.decode('utf-8'))
    os_disk = vm_details['storageProfile']['osDisk']['name']
    data_disks = vm_details['storageProfile']['dataDisks']
    # Create snapshot of the OS disk
    cmd = f"az snapshot create --resource-group {resource_group} --source {os_disk} --name {os_disk}-{SS} --sku Standard_ZRS"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Error creating snapshot for disk {os_disk}: " + result.stderr.decode('utf-8'))
        raise Exception("Error creating snapshot for OS disk")
    logging.info(f"Snapshot created for disk {os_disk}")
    # Create snapshot of the Data disks (in case of multiple data disks)
    # If there is no data disk, the loop will not run
    if data_disks:                
        for disk in data_disks:
            disk_name = disk['name']
            cmd = f"az snapshot create --resource-group {resource_group} --source {disk_name} --name {disk_name}-{SS} --sku Standard_ZRS"
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                logging.error(f"Error creating snapshot for data disk {disk_name}: " + result.stderr.decode('utf-8'))
                raise Exception(f"Error creating snapshot for data disk {disk_name}")
            logging.info(f"Snapshot created for data disk {disk_name}")
    else:
        logging.info(f"No data disks found for VM {vm_name}, hence not creating any snapshots.")

# Function to create a disk from a snapshot in a zone where you are going to create a VM.
def create_disks_from_snapshots():
    # Get the VM details
    cmd = f"az vm show --resource-group {resource_group} --name {vm_name}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error("Error getting VM details: " + result.stderr.decode('utf-8'))
        raise Exception("Error getting VM details")
    vm_details = json.loads(result.stdout.decode('utf-8'))
    os_disk = vm_details['storageProfile']['osDisk']['name']
    data_disks = vm_details['storageProfile']['dataDisks']
    # Capture the snapshot ID of the OS disk and use it to create a disk in the zone and resource group of your choice
    cmd = f"az snapshot show --resource-group {resource_group} --name {os_disk}-{SS}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Error getting snapshot id for disk {os_disk}-{SS}: " + result.stderr.decode('utf-8'))
        raise Exception(f"Error getting snapshot id for OS disk {os_disk}")
    snapshot_details = json.loads(result.stdout.decode('utf-8'))
    snapshot_id = snapshot_details['id']
    logging.info(f"Snapshot ID: {snapshot_id}")
    # Create a disk from the snapshot in the zone of your choice
    cmd = f"az disk create --resource-group {new_vm_rg} --source {snapshot_id} --name {os_disk}-zone{AZ} --zone {AZ}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Error creating disk from snapshot {os_disk}-{SS}: " + result.stderr.decode('utf-8'))
        raise Exception(f"Error creating disk from snapshot {os_disk}")
    logging.info(f"Disk created from snapshot {os_disk}-{SS}")
    # Create snapshot of the Data disks (in case of multiple data disks)
    if data_disks:
        for disk in data_disks:
            disk_name = disk['name']
            # Capture the snapshot ID of the data disk and use it to create a disk in the zone and resource group of your choice
            cmd = f"az snapshot show --resource-group {resource_group} --name {disk_name}-{SS}"
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                logging.error(f"Error getting snapshot id for data disk {disk_name}-{SS}: " + result.stderr.decode('utf-8'))
                raise Exception(f"Error getting snapshot id for data disk {disk_name}")
            snapshot_details = json.loads(result.stdout.decode('utf-8'))
            snapshot_id = snapshot_details['id']
            logging.info(f"Snapshot ID: {snapshot_id}")
            cmd = f"az disk create --resource-group {new_vm_rg} --source {snapshot_id} --name {disk_name}-zone{AZ} --zone {AZ}"
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                logging.error(f"Error creating data disk from snapshot {disk_name}-{SS}: " + result.stderr.decode('utf-8'))
                raise Exception(f"Error creating data disk from snapshot {disk_name}")
            logging.info(f"Data Disk created from snapshot {disk_name}-{SS}")
    else:
        logging.info(f"No data disks found for VM {vm_name}, hence not creating any data disks from snapshot.")

# Create a VM from the disk in the zone of your choice. 
def create_vm_from_disks():
    # Get the VM details
    cmd = f"az vm show --resource-group {resource_group} --name {vm_name}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error("Error getting VM details: " + result.stderr.decode('utf-8'))
        raise Exception("Error getting VM details")
    vm_details = json.loads(result.stdout.decode('utf-8'))
    os_disk = vm_details['storageProfile']['osDisk']['name']
    data_disks = vm_details['storageProfile']['dataDisks']
    # Create a VM from the disk in the zone of your choice
    cmd = f"az vm create --resource-group {new_vm_rg} --name {vm_name}-zone{AZ} --attach-os-disk {os_disk}-zone{AZ} --os-type {OS_TYPE} --zone {AZ} --subnet {subnet_id} --size {VM_SKU} --public-ip-address \"\""
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Error creating VM from disk {os_disk}-zone{AZ}: " + result.stderr.decode('utf-8'))
        raise Exception(f"Error creating VM from disk {os_disk}")
    logging.info(f"VM created from disk {os_disk}-zone{AZ}")
    # Attach data disks to the VM
    if data_disks:
        for disk in data_disks:
            disk_name = disk['name']
            cmd = f"az vm disk attach --resource-group {new_vm_rg} --vm-name {vm_name}-zone{AZ} --name {disk_name}-zone{AZ}"
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                logging.error(f"Error attaching disk to VM: {disk_name}-zone{AZ}: " + result.stderr.decode('utf-8'))
                raise Exception(f"Error attaching disk to VM: {disk_name}-zone{AZ}")
            logging.info(f"Disk attached to VM: {disk_name}-zone{AZ}")
    else:
        logging.info(f"No data disks found for VM {vm_name}, hence not attaching any data disks to the VM.")

# Declare the variables
# Path of the csv file which contains the required details
csv_file = sys.argv[1]

# Initialize logging
logging.basicConfig(filename='snapshot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Capturing the subnet ID that is going to use in VM creation.
try:
    subnet_id = capture_subnet_id()
    # Proceed with the rest of the program using subnet_id
except Exception as e:
    logging.error(f"Error: {str(e)}")
    sys.exit(1)

# Calling the program in a for loop to read the csv file and create snapshots, disks and VMs
#Open the csv file in read mode
with open(csv_file, 'r') as file:
    #Read the csv file
    csv_reader = csv.reader(file)
    #Skip the header
    next(csv_reader)
    #Iterate over the rows in the csv file
    for row in csv_reader:
        if len(row) < 6:
            print('Please provide all the required details in the csv file')
            sys.exit(1)
        #Get the VM name from the csv file
        vm_name = row[0]
        #Get the resource group from the csv file
        resource_group = row[1]
        # Get the OS type from the csv file
        OS_TYPE = row[2]
        # Get the new VM resource group from the csv file
        new_vm_rg = row[3]
        #Get the zone from the csv file
        AZ = int(row[4])
        # Get the VM SKU from the csv file
        VM_SKU = row[5]
        #VM name suffix. It will be appended to the VM name to create a VM in the zone of your choice
        VM_SUFFIX = f"zone-{AZ}"
        #Snapshot suffix. It will be appended to the disk name to create a snapshot
        SS = f"ss-{vm_name}-zone-{AZ}"
        #Calling the function to create snapshots
        try:
            create_snapshots()
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            sys.exit(1)
        #Calling the function to create disks from snapshots
        try:
            create_disks_from_snapshots()
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            sys.exit(1)
        #Calling the function to create VM from disks
        try: 
            create_vm_from_disks()
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            sys.exit(1)
    logging.info("All VMs created successfully.")