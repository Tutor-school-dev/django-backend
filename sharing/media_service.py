"""
Centralized Media Service for handling S3 uploads
Provides a modular, scalable solution for managing media files
"""

import boto3
import uuid
from typing import Optional, Tuple
from django.conf import settings
from botocore.exceptions import ClientError


class MediaType:
    """Enumeration of supported media types"""
    PROFILE_PICTURE = 'profile_pictures'
    PROFILE_VIDEO = 'profile_videos'


class UserType:
    """Enumeration of user types"""
    TUTOR = 'tutor'
    LEARNER = 'learner'


class S3MediaService:
    """
    Centralized service for handling S3 media uploads and management.
    
    Bucket structure:
    - ts-public-data/
      - profile_pictures/
        - tutor/{tutor_id}/
        - learner/{learner_id}/
      - profile_videos/
        - tutor/{tutor_id}/
        - learner/{learner_id}/
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
    
    def _generate_s3_key(
        self, 
        media_type: str, 
        user_type: str, 
        user_id: str, 
        filename: str
    ) -> str:
        """
        Generate S3 key following the standard path structure
        
        Args:
            media_type: Type of media (profile_pictures, profile_videos)
            user_type: Type of user (tutor, learner)
            user_id: UUID of the user
            filename: Original filename with extension
            
        Returns:
            S3 key path: e.g., "profile_pictures/tutor/uuid/filename.jpg"
        """
        # Extract file extension
        file_extension = filename.rsplit('.', 1)[-1] if '.' in filename else ''
        
        # Generate unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}" if file_extension else f"{uuid.uuid4().hex}.bin"
        
        return f"{media_type}/{user_type}/{user_id}/{unique_filename}"
    
    def upload_file(
        self,
        file_obj,
        media_type: str,
        user_type: str,
        user_id: str,
        filename: str,
        content_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file to S3
        
        Args:
            file_obj: File object to upload (Django UploadedFile or file-like object)
            media_type: Type of media (use MediaType constants)
            user_type: Type of user (use UserType constants)
            user_id: UUID of the user
            filename: Original filename
            content_type: MIME type (optional, will be inferred if not provided)
            
        Returns:
            Tuple of (success: bool, s3_key: str, error_message: str)
            
        Example:
            success, s3_key, error = service.upload_file(
                file_obj=request.FILES['profile_pic'],
                media_type=MediaType.PROFILE_PICTURE,
                user_type=UserType.TUTOR,
                user_id=str(teacher.id),
                filename='profile.jpg',
                content_type='image/jpeg'
            )
        """
        try:
            # Validate media type
            valid_media_types = [MediaType.PROFILE_PICTURE, MediaType.PROFILE_VIDEO]
            if media_type not in valid_media_types:
                return False, None, f"Invalid media type. Must be one of: {valid_media_types}"
            
            # Validate user type
            valid_user_types = [UserType.TUTOR, UserType.LEARNER]
            if user_type not in valid_user_types:
                return False, None, f"Invalid user type. Must be one of: {valid_user_types}"
            
            # Generate S3 key
            s3_key = self._generate_s3_key(media_type, user_type, user_id, filename)
            
            # Prepare upload arguments
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file_obj,
            }
            
            # Add content type if provided
            if content_type:
                upload_args['ContentType'] = content_type
            
            # Note: ACL removed - bucket is configured as public via bucket policy
            # If ACLs are needed, they must be enabled at bucket level first
            
            # Upload to S3
            self.s3_client.put_object(**upload_args)
            
            return True, s3_key, None
            
        except ClientError as e:
            error_message = f"S3 upload failed: {str(e)}"
            return False, None, error_message
        except Exception as e:
            error_message = f"Upload failed: {str(e)}"
            return False, None, error_message
    
    def delete_file(self, s3_key: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file from S3
        
        Args:
            s3_key: The S3 key of the file to delete
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True, None
        except ClientError as e:
            error_message = f"S3 deletion failed: {str(e)}"
            return False, error_message
        except Exception as e:
            error_message = f"Deletion failed: {str(e)}"
            return False, error_message
    
    def get_file_url(self, s3_key: str) -> str:
        """
        Get the public URL for an S3 file
        
        Args:
            s3_key: The S3 key of the file
            
        Returns:
            Public URL of the file
        """
        return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    
    def generate_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate a presigned URL for temporary access to a private file
        
        Args:
            s3_key: The S3 key of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Tuple of (success: bool, presigned_url: str, error_message: str)
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return True, url, None
        except ClientError as e:
            error_message = f"Failed to generate presigned URL: {str(e)}"
            return False, None, error_message
    
    def list_user_files(
        self, 
        media_type: str, 
        user_type: str, 
        user_id: str
    ) -> Tuple[bool, list, Optional[str]]:
        """
        List all files for a specific user in a media type
        
        Args:
            media_type: Type of media
            user_type: Type of user
            user_id: UUID of the user
            
        Returns:
            Tuple of (success: bool, files: list, error_message: str)
        """
        try:
            prefix = f"{media_type}/{user_type}/{user_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                files = [
                    {
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'url': self.get_file_url(obj['Key'])
                    }
                    for obj in response['Contents']
                ]
            
            return True, files, None
            
        except ClientError as e:
            error_message = f"Failed to list files: {str(e)}"
            return False, [], error_message
