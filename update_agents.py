import json
import os

import requests
import xmltodict
from dotenv import load_dotenv
from os.path import exists
from base64 import b64encode
from datetime import datetime
import hashlib

## update_agents.py
## Check for and download newer versions of Qualys Cloud Agent binary files, and save to global repository

def log_event(event: str):
    log_file = os.getenv("LOG_FILE")
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}] {event}\n")

def validate_binary(checksum: str, binary_file: bytes):
    # Check the file's SHA-2-256 hash against the provided checksum
    # Return True if matched
    # Return False if not matched
    if os.getenv('DEBUG'):
        event = f"DEBUG: Received check has data - {checksum}"
        print(event)
        log_event(event=event)

    hash_type = checksum.split(':')[0].strip()
    check_hash = checksum.split(':')[1].strip()
    content_hash = None
    match hash_type:
        case 'Hash-SHA-256':
            content_hash = hashlib.sha256(binary_file).hexdigest()
        case 'Hash-SHA-512':
            content_hash = hashlib.sha512(binary_file).hexdigest()
        case 'Hash-SHA-384':
            content_hash = hashlib.sha384(binary_file).hexdigest()

    if content_hash is None:
        event = f"ERROR: Hashing algorithm not supported - {hash_type}"
        print(event)
        log_event(event=event)
        return False

    if os.getenv('DEBUG'):
        event = f"DEBUG: calculated hash - {content_hash}"
        print(event)
        log_event(event=event)

    if content_hash == check_hash:
        return True

    return False

def binary_downloader(base_url: str, headers: dict, repo_dir: str, file_name: str, payload: str,
                      checksum: str) -> bool:
    # Download installer binary file and compare hash with checksum
    # Return True if download successful
    # Return False if download unsuccessful
    # Return False if file save unsuccessful
    binary_response = requests.post(url=f"{base_url}/qps/rest/1.0/download/ca/downloadbinary", headers=headers,
                                    data=payload)
    if binary_response.status_code == 200:
        if validate_binary(checksum=checksum, binary_file=binary_response.content):
            with open(f"{repo_dir}/{file_name}", 'wb') as f:
                f.write(binary_response.content)
            return True
        else:
            event="ERROR: Could not validate checksum for downloaded file"
            print(event)
            log_event(event=event)
    return False

def download_binary_info(baseurl: str, headers: dict, payload: str):
    # Download binary information for Qualys Cloud Agent installer
    # Return binary information as dict if successful
    # Return None if unsuccessful
    info_response = requests.post(url=f"{baseurl}/qps/rest/1.0/process/ca/binaryinfo", headers=headers, data=payload)
    if info_response.status_code == 200:
        return xmltodict.parse(info_response.content)['ServiceResponse']['data']['AllBinaryInfo']['platforms']['Platform']
    else:
        return None

def payload_generator(platform: str = "WINDOWS", arch: str = "X_86_64", request_type: str = "INFO"):
    # Generate payload for requesting binary information or binary installer
    # Return string containing XML payload
    if request_type == "INFO":
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<ServiceRequest>
  <data>
    <BinaryInfo>
      <platform>{platform}</platform>
      <architecture>{arch}</architecture>
    </BinaryInfo>
  </data>
</ServiceRequest>"""
    else:
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<ServiceRequest>
  <data>
    <DownloadBinary>
      <platform>{platform}</platform>
      <architecture>{arch}</architecture>
    </DownloadBinary>
  </data>
</ServiceRequest>"""
    return payload

def new_version(new_info: dict, current_info: dict):
    # Check version information
    # Return False if version in new_info matches version in current_info
    # Otherwise return True
    if new_info['version'] != current_info['version']:
        return True
    else:
        return False

def load_binary_info(info_dir: str, file_name: str):
    # Load binary info file
    # Return info as dict if successful
    # Return None if unsuccessful
    if exists(f"{info_dir}/{file_name}"):
        with open(f"{info_dir}/{file_name}", 'r') as f:
            info_dict = json.loads(f.read())
            return info_dict
    else:
        return None

def main():
    load_dotenv()
    base_url = os.getenv("QUALYS_URL")
    username = os.getenv("QUALYS_USERNAME")
    password = os.getenv("QUALYS_PASSWORD")
    headers = {"Authorization": f"Basic {b64encode(f"{username}:{password}".encode()).decode()}",
               "X-Requested-With": "update_agents.py"}
    repo_dir = os.getenv("REPO_DIRECTORY")
    info_dir = f"{repo_dir}/info"

    if not exists(repo_dir):
        os.makedirs(repo_dir)
        os.makedirs(info_dir)
    elif not exists(info_dir):
        os.makedirs(info_dir)

    for binary in [("WINDOWS","X_86_64"),
                   ("MACOSX","X_64"),
                   ("MACOSX_M_1","ARM_64"),
                   ("LINUX","X_64"),
                   ("LINUX_UBUNTU", "X_64")]:
        platform = binary[0]
        arch = binary[1]
        info_file = f"{platform}_{arch}_info.json"

        # Download binary information for the platform,architecture tuple
        new_info = download_binary_info(baseurl=base_url, headers=headers,
                                        payload=payload_generator(platform=platform,
                                                                  arch=arch,
                                                                  request_type="INFO"))
        if new_info is None:
            event = f"ERROR: Could not download binary info for {platform}/{arch}"
            print(event)
            log_event(event=event)
            continue

        current_info = load_binary_info(info_dir=info_dir, file_name=info_file)
        if current_info is None:
            event = f"WARNING: Could not load binary info from file {info_file}"
            print(event)
            log_event(event=event)

        if current_info is None or new_version(new_info=current_info, current_info=current_info):
            # Download and validate new binary
            binary_file = f"Qualys_Agent_{platform}_{arch}{new_info['extension']}"
            if not binary_downloader(base_url=base_url, headers=headers, repo_dir=repo_dir, file_name=binary_file,
                                     payload=payload_generator(platform=platform,
                                                               arch=arch,
                                                               request_type="BINARY"),
                                     checksum=new_info['hash']):
                event = f"ERROR: Could not download binary info for {platform}/{arch}"
                print(event)
                log_event(event=event)
                continue

            # Add filename to new info file and write to disk
            new_info['File'] = binary_file
            with open(f"{info_dir}/{info_file}", 'w') as f:
                f.write(json.dumps(new_info, indent=4))

            event=f"Updated {platform}/{arch} : File {binary_file}, version {new_info['version']}"
            print(event)
            log_event(event=event)
        else:
            event=f"Skipped {platform}/{arch}, no new version available"
            print(event)
            log_event(event=event)

if __name__ == "__main__":
    main()