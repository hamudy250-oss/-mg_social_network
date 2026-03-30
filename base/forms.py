from django import forms
from django.core.exceptions import ValidationError

from .models import Profile
from .validators import FileSizeValidator, validate_image_file_extension


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'cover_photo', 'bio', 'location', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'اكتب نبذة قصيرة عن نفسك...',
                'class': 'w-full rounded-3xl border border-slate-700 bg-[#0b1120] px-4 py-3 text-sm text-white outline-none focus:border-purple-500',
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'الموقع',
                'class': 'w-full rounded-3xl border border-slate-700 bg-[#0b1120] px-4 py-3 text-sm text-white outline-none focus:border-purple-500',
            }),
            'website': forms.URLInput(attrs={
                'placeholder': 'https://example.com',
                'class': 'w-full rounded-3xl border border-slate-700 bg-[#0b1120] px-4 py-3 text-sm text-white outline-none focus:border-purple-500',
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'mt-3 w-full rounded-3xl border border-slate-700 bg-[#0b1120] p-3 text-sm text-white cursor-pointer',
                'accept': 'image/*',
            }),
            'cover_photo': forms.ClearableFileInput(attrs={
                'class': 'mt-3 w-full rounded-3xl border border-slate-700 bg-[#0b1120] p-3 text-sm text-white cursor-pointer',
                'accept': 'image/*',
            }),
        }
        labels = {
            'avatar': 'الصورة الشخصية',
            'cover_photo': 'صورة الغلاف',
            'bio': 'نبذة',
            'location': 'الموقع',
            'website': 'الموقع الإلكتروني',
        }
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            validate_image_file_extension(avatar)
            FileSizeValidator(2)(avatar)
        return avatar

    def clean_cover_photo(self):
        cover_photo = self.cleaned_data.get('cover_photo')
        if cover_photo:
            validate_image_file_extension(cover_photo)
            FileSizeValidator(4)(cover_photo)
        return cover_photo

    def clean_bio(self):
        return (self.cleaned_data.get('bio') or '').strip()

    def clean_location(self):
        return (self.cleaned_data.get('location') or '').strip()

    def clean_website(self):
        website = self.cleaned_data.get('website')
        return website.strip() if website else website
