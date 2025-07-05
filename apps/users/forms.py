from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username') if 'username' in cleaned_data else None
        password = cleaned_data.get('password') if 'password' in cleaned_data else None

        if username and password:
            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError(_("Incorrect username or password."))
            elif getattr(self.user, 'deleted', False):
                raise forms.ValidationError(_("This account has been deleted."))
            elif not self.user.is_active:
                raise forms.ValidationError(_("This account has been blocked."))

        return cleaned_data



class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'phone', 'comment']
        help_texts = {
            'username': _("Only alphabets (a-zA-Z), max 32 characters."),
            'phone': _("Format: '+255000000000'. Up to 12 digits allowed.")
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if not username:
            raise forms.ValidationError(_("Username cannot be blank."))

        # Apply the same cleaning logic as in the model's clean method
        username = username.strip()
        if username:
            username = username[0].upper() + username[1:].lower()
        else:
            raise forms.ValidationError(_("Username cannot be empty."))

        # Check for uniqueness after cleaning
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("This username is already taken. Please choose another."))

        # Re-run the model's validator for username to ensure it meets regex requirements
        try:
            User.username_validator(username)
        except RegexValidator as e:
            raise forms.ValidationError(e.message)

        return username

    def clean_fullname(self):
        fullname = self.cleaned_data['fullname']
        if not fullname:
            raise forms.ValidationError(_("Full name cannot be blank."))

        # Apply the same cleaning logic as in the model's clean method
        names = fullname.strip().split(' ')
        cleaned_names = []
        for name in names:
            if name:
                cleaned_names.append(name[0].upper() + name[1:].lower())
        
        # Recombine, or raise error if all parts become empty after cleaning
        fullname = ' '.join(cleaned_names) if cleaned_names else None
        if not fullname:
            raise forms.ValidationError(_("Full name cannot be empty."))
        elif len(fullname) < 5:
            raise forms.ValidationError(_("Full name should exceed 5 characters."))
        return fullname

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            validator = User.phone_validator
            try:
                validator(phone)
            except RegexValidator as e:
                raise forms.ValidationError(e.message)
        return phone if phone else None
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        return None if comment in ("", "-") else comment

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['username'].upper())
        if commit:
            user.save()
        return user
    