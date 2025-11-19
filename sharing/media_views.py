from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from auth_app.authentication import JWTAuthentication
from sharing.media_service import S3MediaService, MediaType, UserType
from sharing.media_serializers import MediaUploadSerializer


class MediaUploadView(APIView):
    """
    Protected endpoint for uploading media files to S3
    Supports both tutors and learners
    """
    authentication_classes = []  # Manual authentication
    permission_classes = []
    
    def post(self, request):
        """
        Upload a media file to S3
        
        Expected headers:
        Authorization: Bearer <jwt_token>
        
        Expected body (multipart/form-data):
        - file: The file to upload
        - media_type: 'profile_pictures' or 'profile_videos'
        
        Example using curl:
        curl -X POST http://localhost:8000/api/media/upload/ \
          -H "Authorization: Bearer <token>" \
          -F "file=@/path/to/image.jpg" \
          -F "media_type=profile_pictures"
        """
        # Authenticate the request
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        user_type = getattr(user, 'user_type', None)
        
        if not user_type:
            return Response(
                {'error': 'Invalid user type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate request data
        serializer = MediaUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = serializer.validated_data['file']
        media_type = serializer.validated_data['media_type']
        
        # Initialize S3 service
        media_service = S3MediaService()
        
        # Upload file to S3
        success, s3_key, error_message = media_service.upload_file(
            file_obj=file_obj,
            media_type=media_type,
            user_type=user_type,
            user_id=str(user.id),
            filename=file_obj.name,
            content_type=file_obj.content_type
        )
        
        if not success:
            return Response(
                {'error': error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Generate public URL
        file_url = media_service.get_file_url(s3_key)
        
        # Update user model with the new media URL
        if media_type == MediaType.PROFILE_PICTURE:
            user.profile_pic = s3_key
            user.save(update_fields=['profile_pic'])
        elif media_type == MediaType.PROFILE_VIDEO:
            user.video_url = s3_key
            user.save(update_fields=['video_url'])
        
        return Response({
            'message': 'File uploaded successfully',
            's3_key': s3_key,
            'url': file_url,
            'media_type': media_type,
            'user_type': user_type
        }, status=status.HTTP_201_CREATED)


class MediaDeleteView(APIView):
    """
    Protected endpoint for deleting media files from S3
    """
    authentication_classes = []
    permission_classes = []
    
    def delete(self, request):
        """
        Delete a media file from S3
        
        Expected headers:
        Authorization: Bearer <jwt_token>
        
        Expected body:
        {
            "s3_key": "profile_pictures/tutor/uuid/filename.jpg"
        }
        """
        # Authenticate the request
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        
        s3_key = request.data.get('s3_key')
        
        if not s3_key:
            return Response(
                {'error': 's3_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the S3 key belongs to the authenticated user
        user_id = str(user.id)
        if user_id not in s3_key:
            return Response(
                {'error': 'You can only delete your own files'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete from S3
        media_service = S3MediaService()
        success, error_message = media_service.delete_file(s3_key)
        
        if not success:
            return Response(
                {'error': error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Clear the field in user model if it matches
        if hasattr(user, 'profile_pic') and user.profile_pic == s3_key:
            user.profile_pic = ''
            user.save(update_fields=['profile_pic'])
        elif hasattr(user, 'video_url') and user.video_url == s3_key:
            user.video_url = ''
            user.save(update_fields=['video_url'])
        
        return Response({
            'message': 'File deleted successfully',
            's3_key': s3_key
        }, status=status.HTTP_200_OK)


class MediaListView(APIView):
    """
    Protected endpoint to list all media files for the authenticated user
    """
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        """
        List all media files for the authenticated user
        
        Expected headers:
        Authorization: Bearer <jwt_token>
        
        Query parameters (optional):
        - media_type: Filter by 'profile_pictures' or 'profile_videos'
        """
        # Authenticate the request
        auth = JWTAuthentication()
        auth_result = auth.authenticate(request)
        
        if not auth_result:
            return Response(
                {'error': 'Authentication credentials were not provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user, token = auth_result
        user_type = getattr(user, 'user_type', None)
        
        media_type = request.query_params.get('media_type')
        
        # Initialize S3 service
        media_service = S3MediaService()
        
        result = {}
        
        # If media_type specified, list only that type
        if media_type:
            if media_type not in [MediaType.PROFILE_PICTURE, MediaType.PROFILE_VIDEO]:
                return Response(
                    {'error': 'Invalid media_type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success, files, error_message = media_service.list_user_files(
                media_type=media_type,
                user_type=user_type,
                user_id=str(user.id)
            )
            
            if not success:
                return Response(
                    {'error': error_message},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            result[media_type] = files
        else:
            # List all media types
            for mt in [MediaType.PROFILE_PICTURE, MediaType.PROFILE_VIDEO]:
                success, files, error_message = media_service.list_user_files(
                    media_type=mt,
                    user_type=user_type,
                    user_id=str(user.id)
                )
                
                if success:
                    result[mt] = files
        
        return Response({
            'user_id': str(user.id),
            'user_type': user_type,
            'media': result
        }, status=status.HTTP_200_OK)
