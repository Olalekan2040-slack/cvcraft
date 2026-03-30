from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Profile
        fields = ['avatar', 'job_title', 'bio', 'linkedin_url', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
