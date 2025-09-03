#!/usr/bin/env python3
"""
Script to copy export profiles and their schedules
from a source PIM instance to a target PIM instance
"""

import requests
import argparse
import json
import os
import sys
from typing import Dict, List, Optional

class PIMExportCopier:
    def __init__(self, source_url: str, source_bearer: str, target_url: str, target_bearer: str):
        """
        Initialize the copier with URLs and tokens for source and target instances
        
        Args:
            source_url: Source instance URL (ex: https://SOURCE.quable.com)
            source_bearer: Bearer token for source instance
            target_url: Target instance URL (ex: https://TARGET.quable.com)
            target_bearer: Bearer token for target instance
        """
        self.source_url = source_url.rstrip('/')
        self.source_bearer = source_bearer
        self.target_url = target_url.rstrip('/')
        self.target_bearer = target_bearer
        
        # Mapping of old IDs to new profile IDs
        self.profile_id_mapping = {}
        
    def _make_request(self, method: str, url: str, bearer: str, data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, PUT)
            url: Complete URL
            bearer: Bearer token
            data: Data to send (for POST/PUT)
            
        Returns:
            JSON response
        """
        headers = {
            'Authorization': f'Bearer {bearer}',
            'Content-Type': 'application/json' if data else 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error during {method} request to {url}: {e}")
            if hasattr(e.response, 'text'):
                print(f"Error details: {e.response.text}")
            raise

    def _clean_mapping_element(self, element):
        """
        Clean a mapping element by removing unwanted fields
        
        Args:
            element: Element to clean (dict, list, or other)
            
        Returns:
            Cleaned element
        """
        if isinstance(element, dict):
            cleaned = element.copy()
            # Remove unwanted fields
            cleaned.pop('@id', None)
            cleaned.pop('@type', None)
            
            # Remove options if array is empty
            if 'options' in cleaned and isinstance(cleaned['options'], list) and len(cleaned['options']) == 0:
                cleaned.pop('options', None)
            
            # Recursive cleaning of values
            for key, value in cleaned.items():
                cleaned[key] = self._clean_mapping_element(value)
                
            return cleaned
            
        elif isinstance(element, list):
            return [self._clean_mapping_element(item) for item in element]
        else:
            return element

    def _sanitize_upload_location(self, upload_location: str) -> str:
        """
        Mask password in SFTP URL
        
        Args:
            upload_location: SFTP URL with potential password
            
        Returns:
            SFTP URL with masked password
        """
        if not upload_location or not upload_location.startswith('sftp://') or not upload_location.startswith('ftp://'):
            return upload_location
        
        try:
            # Format: sftp://USER:PASSWORD@HOST/PATH
            # Look for USER:PASSWORD@ pattern
            if '@' in upload_location and ':' in upload_location:
                # Find part before @
                before_at = upload_location.split('@')[0]  # sftp://USER:PASSWORD
                after_at = upload_location.split('@', 1)[1]  # HOST/PATH
                
                # Check if there's a password (presence of :)
                if ':' in before_at:
                    protocol_user = before_at.rsplit(':', 1)[0]  # sftp://USER
                    # Reconstruct URL with masked password
                    sanitized = f"{protocol_user}:***@{after_at}"
                    return sanitized
            
            # If no password detected, return original URL
            return upload_location
            
        except Exception:
            # In case of parsing error, return original URL
            return upload_location

    def get_target_export_profiles(self) -> List[Dict]:
        """
        Retrieve all export profiles from target instance
        
        Returns:
            List of existing export profiles on target
        """
        print("🔄 Retrieving existing export profiles from target...")
        
        try:
            url = f"https://{self.target_url}.quable.com/api/export-profiles"
            response = self._make_request('GET', url, self.target_bearer)
            
            profiles = response.get('hydra:member', [])
            print(f"✅ {len(profiles)} existing export profiles found on target")
            
            return profiles
        except Exception as e:
            print(f"⚠️ Error retrieving target profiles: {e}")
            return []
    
    def get_source_export_profiles(self) -> List[Dict]:
        """
        Retrieve all export profiles from source instance
        
        Returns:
            List of export profiles
        """
        print("🔄 Retrieving export profiles from source...")
        
        url = f"https://{self.source_url}.quable.com/api/export-profiles"
        response = self._make_request('GET', url, self.source_bearer)
        
        profiles = response.get('hydra:member', [])
        print(f"✅ {len(profiles)} export profiles retrieved")
        
        return profiles
    
    def get_source_export_schedules(self) -> List[Dict]:
        """
        Retrieve all export schedules from source instance
        
        Returns:
            List of export schedules
        """
        print("🔄 Retrieving export schedules from source...")
        
        url = f"https://{self.source_url}.quable.com/api/plannings/exports"
        response = self._make_request('GET', url, self.source_bearer)
        
        schedules = response.get('hydra:member', [])
        print(f"✅ {len(schedules)} export schedules retrieved")
        
        return schedules
    
    def create_or_update_target_export_profile(self, profile: Dict, target_profiles: List[Dict]) -> str:
        """
        Create or update an export profile on target instance
        
        Args:
            profile: Export profile to create/update
            target_profiles: List of existing profiles on target
            
        Returns:
            ID of created or updated profile
        """
        # Copy profile
        profile_data = profile.copy()
        old_id = profile_data.pop('id', None)
        profile_name = profile_data.get('name', 'Unnamed')
        
        # Search for existing profile with same name
        existing_profile = None
        for target_profile in target_profiles:
            if target_profile.get('name') == profile_name:
                existing_profile = target_profile
                break
        
        # Remove metadata fields that shouldn't be sent
        profile_data.pop('@type', None)
        profile_data.pop('@id', None)
        profile_data.pop('dateCreated', None)
        profile_data.pop('dateModified', None)
        profile_data.pop('createdBy', None)
        profile_data.pop('updatedBy', None)
        
        # Clean mappings
        if 'mappings' in profile_data and isinstance(profile_data['mappings'], list):
            profile_data['mappings'] = [self._clean_mapping_element(mapping) for mapping in profile_data['mappings']]
        
        if existing_profile:
            # Update existing profile (PUT)
            existing_id = existing_profile.get('id')
            print(f"🔄 Updating existing profile '{profile_name}' (ID: {existing_id})...")
            
            url = f"https://{self.target_url}.quable.com/api/export-profiles/{existing_id}"
            response = self._make_request('PUT', url, self.target_bearer, profile_data)
            
            new_id = response.get('id', existing_id)
            if new_id and old_id:
                self.profile_id_mapping[old_id] = new_id
                
            print(f"✅ Profile updated with ID: {new_id}")
            return new_id
        else:
            # Create new profile (POST)
            print(f"🔄 Creating new profile '{profile_name}'...")
            
            url = f"https://{self.target_url}.quable.com/api/export-profiles"
            response = self._make_request('POST', url, self.target_bearer, profile_data)
            
            new_id = response.get('id')
            if new_id and old_id:
                self.profile_id_mapping[old_id] = new_id
                
            print(f"✅ Profile created with ID: {new_id}")
            return new_id
    
    def create_target_export_schedule(self, schedule: Dict) -> str:
        """
        Create an export schedule on target instance
        
        Args:
            schedule: Export schedule to create
            
        Returns:
            ID of new created schedule
        """
        # Copy schedule and remove ID for creation
        schedule_data = schedule.copy()
        old_id = schedule_data.pop('id', None)
        
        # Remove metadata fields that shouldn't be sent
        schedule_data.pop('@type', None)
        schedule_data.pop('@id', None)
        schedule_data.pop('dateCreated', None)
        schedule_data.pop('dateModified', None)
        schedule_data.pop('createdBy', None)
        schedule_data.pop('updatedBy', None)
        
        # Replace exportProfileId with new ID
        if 'export' in schedule_data and 'exportProfileId' in schedule_data['export']:
            old_profile_id = schedule_data['export']['exportProfileId']
            new_profile_id = self.profile_id_mapping.get(old_profile_id)
            
            if new_profile_id:
                schedule_data['export']['exportProfileId'] = new_profile_id
                
                # Mask password in uploadLocation if present
                if 'uploadLocation' in schedule_data['export']:
                    original_location = schedule_data['export']['uploadLocation']
                    schedule_data['export']['uploadLocation'] = self._sanitize_upload_location(original_location)
                
                print(f"🔄 Creating schedule '{schedule_data.get('name', 'Unnamed')}'...")
                print(f"   Old profile ID: {old_profile_id} → New profile ID: {new_profile_id}")
                
                # Display masked uploadLocation if it exists
                if 'uploadLocation' in schedule_data['export']:
                    print(f"   Upload Location: {schedule_data['export']['uploadLocation']}")
            else:
                print(f"⚠️  Profile ID {old_profile_id} not found in mapping, schedule ignored")
                return None
        
        url = f"https://{self.target_url}.quable.com/api/plannings/exports"
        response = self._make_request('POST', url, self.target_bearer, schedule_data)
        
        new_id = response.get('id')
        print(f"✅ Schedule created with ID: {new_id}")
        return new_id
    
    def copy_all_export_data(self):
        """
        Copy all export profiles and their schedules from source to target
        """
        print("🚀 Starting export data copy")
        print("=" * 50)
        
        try:
            # Step 1: Retrieve existing export profiles on target
            target_profiles = self.get_target_export_profiles()
            
            # Step 2: Retrieve source export profiles
            source_profiles = self.get_source_export_profiles()
            
            # Step 3: Create/update profiles on target
            print("\n📝 Creating/updating export profiles on target...")
            processed_profiles = 0
            for profile in source_profiles:
                try:
                    self.create_or_update_target_export_profile(profile, target_profiles)
                    processed_profiles += 1
                except Exception as e:
                    print(f"❌ Error processing profile '{profile.get('name', 'Unnamed')}': {e}")
            
            print(f"\n✅ {processed_profiles}/{len(source_profiles)} export profiles processed")
            
            # Step 4: Retrieve export schedules
            source_schedules = self.get_source_export_schedules()
            
            # Step 5: Create schedules on target
            print("\n📅 Creating export schedules on target...")
            created_schedules = 0
            for schedule in source_schedules:
                try:
                    result = self.create_target_export_schedule(schedule)
                    if result:
                        created_schedules += 1
                except Exception as e:
                    print(f"❌ Error creating schedule '{schedule.get('name', 'Unnamed')}': {e}")
            
            print(f"\n✅ {created_schedules}/{len(source_schedules)} export schedules created")
            
            # Summary
            print("\n" + "=" * 50)
            print("🎉 Copy completed successfully!")
            print(f"   • Export profiles processed: {processed_profiles}")
            print(f"   • Schedules copied: {created_schedules}")
            
            if self.profile_id_mapping:
                print("\n📋 Profile ID mapping:")
                for old_id, new_id in self.profile_id_mapping.items():
                    print(f"   {old_id} → {new_id}")
                    
        except Exception as e:
            print(f"\n❌ Critical error during copy: {e}")
            sys.exit(1)


def main():
    """
    Main function - Configure and launch copy
    """
    # Command line arguments configuration
    parser = argparse.ArgumentParser(
        description="Copy export profiles and schedules from one PIM instance to another",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python dataflow-copy.py --source https://source.quable.com --target https://target.quable.com \\
                   --source-bearer "token123" --target-bearer "token456"
        
  python dataflow-copy.py -s https://source.quable.com -t https://target.quable.com \\
                   -sb "token123" -tb "token456"
        """
    )
    
    parser.add_argument(
        '--source', '-s',
        required=True,
        help='Source instance URL (ex: https://source.quable.com)'
    )
    
    parser.add_argument(
        '--target', '-t',
        required=True,
        help='Target instance URL (ex: https://target.quable.com)'
    )
    
    parser.add_argument(
        '--source-bearer', '-sb',
        required=True,
        help='Bearer token for source instance'
    )
    
    parser.add_argument(
        '--target-bearer', '-tb',
        required=True,
        help='Bearer token for target instance'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Display parameters (without full tokens for security)
    print("🔧 Configuration:")
    print(f"   Source: {args.source}")
    print(f"   Target: {args.target}")
    print(f"   Source Bearer: {'*' * (len(args.source_bearer) - 4)}{args.source_bearer[-4:] if len(args.source_bearer) > 4 else '****'}")
    print(f"   Target Bearer: {'*' * (len(args.target_bearer) - 4)}{args.target_bearer[-4:] if len(args.target_bearer) > 4 else '****'}")
    print()
    
    # Create and launch copier
    copier = PIMExportCopier(args.source, args.source_bearer, args.target, args.target_bearer)
    copier.copy_all_export_data()


if __name__ == "__main__":
    main()