import re
from django import forms
from .models import Shop, Product
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['names', 'abbrev', 'comment']
        help_texts = {
            'names': 'The full, descriptive name of the shop.',
            'abbrev': 'A unique, short code or name for the shop.',
            'comment': 'Optional: Add any additional details or notes.',
        }

    def clean_names(self):
        names = self.cleaned_data['names']
        if names:
            names = names.strip()
            if not names:
                raise forms.ValidationError("Shop name cannot be blank.")
            
            if len(names) < 5 or len(names) > 255:
                raise forms.ValidationError("Shop name must be between 5 and 255 characters long.")
            
        return names
    
    def clean_abbrev(self):
        abbrev = self.cleaned_data['abbrev']
        if abbrev:
            abbrev = abbrev.strip().upper()
            if not abbrev:
                raise forms.ValidationError("Abbrev cannot be blank.")
            
            if len(abbrev) < 2 or len(abbrev) > 10:
                raise forms.ValidationError("Abbrev must be between 2 and 10 characters long.")
            
            if not re.fullmatch(r'[A-Z]+', abbrev):
                raise forms.ValidationError("Abbrev must contain only letters A–Z.")
        
            if Shop.objects.filter(abbrev=abbrev).exists():
                raise forms.ValidationError("This abbrev is already in use. Please choose another.")
            
        return abbrev

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()

        if comment and len(comment) > 500:
            raise forms.ValidationError("Comment must be 500 characters or less.")
        
        return None if comment in ("", "-", "N/A") else comment

    def save(self, commit=True):
        duka = super().save(commit=False)
        if commit:
            duka.save()
        return duka
    

class ShopUpdateForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['names', 'abbrev', 'comment']
        help_texts = {
            'names': 'The full, descriptive name of the shop.',
            'abbrev': 'A unique, short code or name for the shop.',
            'comment': 'Optional: Add any additional details or notes.',
        }
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean_names(self):
        names = self.cleaned_data['names']
        if names:
            names = names.strip()
            if not names:
                raise forms.ValidationError("Shop name cannot be blank.")
            
            if len(names) < 5 or len(names) > 255:
                raise forms.ValidationError("Shop name must be between 5 and 255 characters long.")
            
        return names
    
    def clean_abbrev(self):
        abbrev = self.cleaned_data['abbrev']
        if abbrev:
            abbrev = abbrev.strip().upper()
            if not abbrev:
                raise forms.ValidationError("Abbrev cannot be blank.")
            
            if len(abbrev) < 2 or len(abbrev) > 10:
                raise forms.ValidationError("Abbrev must be between 2 and 10 characters long.")
            
            if not re.fullmatch(r'[A-Z]+', abbrev):
                raise forms.ValidationError("Abbrev must contain only letters A–Z.")

            existing_abbrev = Shop.objects.filter(abbrev=abbrev).exclude(pk=self.instance.pk)
            if existing_abbrev.exists():
                raise forms.ValidationError("This abbrev is already in use. Please choose another.")
            
        return abbrev

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()

        if comment and len(comment) > 500:
            raise forms.ValidationError("Comment must be 500 characters or less.")
        
        return None if comment in ("", "-", "N/A") else comment

    def save(self, commit=True):
        duka = super().save(commit=False)
        if commit:
            duka.save()
        return duka


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['shop', 'name', 'qty', 'cost', 'price', 'expiry_date', 'comment']

    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.fullmatch(r"[\w\s.,!?'\"&()@#*-/À-ÿ]+", name):
            raise forms.ValidationError("Invalid product names.")
        return name
    
    def clean_qty(self):
        qty = self.cleaned_data['qty']
        if qty < 1:
            raise forms.ValidationError(_("Quantity cannot be less than 1"))
        return qty
    
    def clean_cost(self):
        cost = self.cleaned_data['cost']
        if cost < 0:
            raise forms.ValidationError(_("Cost cannot be less than 0"))
        return cost
    
    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError(_("Price cannot be less than 0"))
        return price

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if comment and len(comment) > 500:
            raise forms.ValidationError("Comment must be 500 characters or less.")
        return None if comment in ("", "-", "N/A") else comment

    def save(self, commit=True):
        product = super().save(commit=False)
        if commit:
            product.save()
        return product
    

class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['shop', 'name', 'qty', 'cost', 'price', 'expiry_date', 'comment']
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.fullmatch(r"[\w\s.,!?'\"&()@#*-/À-ÿ]+", name):
            raise forms.ValidationError("Invalid product names.")
        return name
    
    def clean_qty(self):
        qty = self.cleaned_data['qty']
        if qty < 0:
            raise forms.ValidationError(_("Quantity cannot be less than 0"))
        return qty
    
    def clean_cost(self):
        cost = self.cleaned_data['cost']
        if cost < 0:
            raise forms.ValidationError(_("Cost cannot be less than 0"))
        return cost
    
    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError(_("Price cannot be less than 0"))
        return price

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if comment and len(comment) > 500:
            raise forms.ValidationError("Comment must be 500 characters or less.")
        return None if comment in ("", "-", "N/A") else comment

    def save(self, commit=True):
        product = super().save(commit=False)
        if commit:
            product.save()
        return product

