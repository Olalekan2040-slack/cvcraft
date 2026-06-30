from django import forms
from allauth.account.forms import SignupForm
from .models import Profile


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save(update_fields=['first_name', 'last_name'])
        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Profile
        fields = ['avatar', 'job_title', 'bio', 'linkedin_url', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
