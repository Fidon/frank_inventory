from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import re

User = get_user_model()


# Authentication form for user login
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


# New user registration form
class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'phone', 'shop', 'comment']
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

        # Re-run the model's validator for username to ensure it meets regex requirements
        try:
            User.username_validator(username)
        except ValidationError as e:
            raise forms.ValidationError(e.message)
        
        # Check for uniqueness after cleaning
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("This username is already taken. Please choose another."))

        return username

    def clean_fullname(self):
        fullname = self.cleaned_data.get('fullname', '').strip()
        if not fullname:
            raise forms.ValidationError(_("Full name cannot be blank."))

        # Split and clean names
        names = fullname.split()
        if len(names) not in (2, 3):
            raise forms.ValidationError(_("Full name must contain 2 or 3 names."))

        cleaned_names = []
        for name in names:
            name = name.strip()
            if not (3 <= len(name) <= 32):
                raise forms.ValidationError(_("Each name must be 3 to 32 characters long."))
            if not re.fullmatch(r"[A-Za-z'\\-]+", name):
                raise forms.ValidationError(_("Names can only contain letters, apostrophes, and hyphens."))
            # Normalize casing
            cleaned_names.append(name[0].upper() + name[1:].lower())

        fullname = ' '.join(cleaned_names)
        return fullname

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            try:
                User.phone_validator(phone)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
            
            # Check for uniqueness
            if User.objects.filter(phone=phone, deleted=False).exists():
                raise forms.ValidationError(_("This phone number is already taken. Please choose another."))
        
        return phone if phone else None
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        return None if comment in ("", "-", "N/A") else comment

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['username'].upper())
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'phone', 'shop', 'comment']
        help_texts = {
            'username': _("Only alphabets (a-zA-Z), max 32 characters."),
            'phone': _("Format: '+255000000000'. Up to 12 digits allowed.")
        }

    def __init__(self, *args, **kwargs):
        # self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

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

        # Re-run the model's validator for username to ensure it meets regex requirements
        try:
            User.username_validator(username)
        except ValidationError as e:
            raise forms.ValidationError(e.message)
        
        # Check for uniqueness (exclude current user)
        existing_user = User.objects.filter(username=username).exclude(pk=self.instance.pk)
        if existing_user.exists():
            raise forms.ValidationError(_("This username is already taken. Please choose another."))

        return username

    def clean_fullname(self):
        fullname = self.cleaned_data.get('fullname', '').strip()
        if not fullname:
            raise forms.ValidationError(_("Full name cannot be blank."))

        # Split and clean names
        names = fullname.split()
        if len(names) not in (2, 3):
            raise forms.ValidationError(_("Full name must contain 2 or 3 names."))

        cleaned_names = []
        for name in names:
            name = name.strip()
            if not (3 <= len(name) <= 32):
                raise forms.ValidationError(_("Each name must be 3 to 32 characters long."))
            if not re.fullmatch(r"[A-Za-z'\\-]+", name):
                raise forms.ValidationError(_("Names can only contain letters, apostrophes, and hyphens."))
            # Normalize casing
            cleaned_names.append(name[0].upper() + name[1:].lower())

        fullname = ' '.join(cleaned_names)
        return fullname

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            try:
                User.phone_validator(phone)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
            
            # Check for uniqueness (exclude current user)
            existing_user = User.objects.filter(phone=phone, deleted=False).exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError(_("This phone number is already taken. Please choose another."))
            
        return phone if phone else None
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        return None if comment in ("", "-", "N/A") else comment

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
