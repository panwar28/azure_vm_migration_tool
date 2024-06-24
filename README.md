# Azure VM Migration Tool

## Overview
This tool automates the migration of virtual machines (VMs) along with its data disks within Microsoft Azure across different zones. It streamlines the process by creating VMs using the OS disks, attaching all the data disks to the target VM, and ensuring a smooth transition between zones.

## Features
- **VM Creation and Data Disk Attachment:** Simplifies the creation of VMs using OS disks and attaches all necessary data disks to the target VM.
- **Logging:** Provides comprehensive logging capabilities to monitor the migration process and identify any potential issues.

## Requirements
- Python 3.6.x
- Azure CLI installed and configured on the machine running the script.
- Appropriate permissions to create and manage snapshots, disks, and VMs within your Azure subscription.

## Installation
1. Clone this repository to your local machine.
2. Ensure Python 3.6.x is installed on your system.
3. Ensure Azure Cli is installed on your system.


## Usage
Before running the script, make sure you are logged in to your Azure account through the Azure CLI and have set the correct subscription context.
Update the network variables in the script so that script can pull subnet id where the VMs need to be attached to. 
Update the attached sample csv with the required details and pass it along with the tool and it will take care of the rest. 

To run the script, use the following command:
# python az_vm_migration_tool.py <csv file name>


## Configuration
The script requires certain parameters to be set before running. These include the source and target zones, as well as the disk ID of the data disk to be migrated. These can be configured within the script itself or passed as command-line arguments.

## Contributing
Contributions to this project are welcome. Please fork the repository, make your changes, and submit a pull request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.