from rest_framework import serializers


class MediaUploadSerializer(serializers.Serializer):
    """Serializer for media upload requests"""
    
    MEDIA_TYPE_CHOICES = ['profile_pictures', 'profile_videos']
    
    file = serializers.FileField(required=True)
    media_type = serializers.ChoiceField(
        choices=MEDIA_TYPE_CHOICES,
        required=True,
        error_messages={'invalid_choice': 'Media type must be one of: profile_pictures, profile_videos'}
    )
    
    def validate_file(self, value):
        """Validate file size and type"""
        max_size = 10 * 1024 * 1024  # 10MB
        
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size / (1024 * 1024)}MB"
            )
        
        return value
    
    def validate(self, data):
        """Cross-field validation for media type and file"""
        media_type = data.get('media_type')
        file = data.get('file')
        
        if media_type == 'profile_pictures':
            # Validate image files
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            allowed_content_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            
            file_extension = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
            
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError({
                    'file': f'Invalid image format. Allowed formats: {", ".join(allowed_extensions)}'
                })
            
            if file.content_type not in allowed_content_types:
                raise serializers.ValidationError({
                    'file': f'Invalid content type. Must be an image file.'
                })
        
        elif media_type == 'profile_videos':
            # Validate video files
            allowed_extensions = ['mp4', 'mov', 'avi', 'mkv', 'webm']
            allowed_content_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm']
            
            file_extension = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
            
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError({
                    'file': f'Invalid video format. Allowed formats: {", ".join(allowed_extensions)}'
                })
            
            # Video files might have various content types, so we're more lenient
            if not file.content_type.startswith('video/'):
                raise serializers.ValidationError({
                    'file': f'Invalid content type. Must be a video file.'
                })
        
        return data
