from django.contrib.auth.forms import UserCreationForm, forms
from django.contrib.auth.models import User
from django import forms
from .models import Company, Product, ProductStatus, SalesProcess

class UserRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'password1', 'password2', 'email', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class CompanyRegistrationForm(forms.ModelForm):
    class Meta:
        model=Company
        exclude= ['user']
        

class DetailRegistrationForm(forms.ModelForm):
    class Meta:
        model= SalesProcess
        exclude= ['company']
        
class ProductSelectionForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    status = forms.ChoiceField(choices=ProductStatus.STATUS_CHOICES)
    description = forms.CharField(widget=forms.Textarea)
    class Meta:
        model= Product, ProductStatus
        fields= '__all__'