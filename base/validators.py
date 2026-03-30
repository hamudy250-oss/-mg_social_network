from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
VIDEO_EXTENSIONS = ['mp4', 'mov', 'webm', 'avi', 'mkv']
ATTACHMENT_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS


def validate_attachment_file_extension(value):
    validator = FileExtensionValidator(allowed_extensions=ATTACHMENT_EXTENSIONS)
    validator(value)


@deconstructible
class FileSizeValidator:
    def __init__(self, max_mb):
        self.max_mb = max_mb
        self.message = f'File size must not exceed {self.max_mb} MB.'

    def __call__(self, value):
        if hasattr(value, 'size') and value.size > self.max_mb * 1024 * 1024:
            raise ValidationError(self.message)

    def __eq__(self, other):
        return isinstance(other, FileSizeValidator) and self.max_mb == other.max_mb


def validate_image_file_extension(value):
    validator = FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)
    validator(value)


def validate_video_file_extension(value):
    validator = FileExtensionValidator(allowed_extensions=VIDEO_EXTENSIONS)
    validator(value)
