from django import forms

from .models import Profile


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
