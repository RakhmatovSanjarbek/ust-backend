from django import forms
from .models import User

class MyUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Parol",
        help_text="Kamida 8 ta belgidan iborat murakkab parol kiriting."
    )
    is_staff = forms.BooleanField(
        required=False,
        initial=True, # Admin qo'shayotganimiz uchun avtomatik belgilangan bo'ladi
        label="Xodim statusi",
        help_text="Admin panelga kirish huquqini beradi."
    )

    class Meta:
        model = User
        # Modelingizda bor majburiy maydonlarni kiriting
        fields = ('phone', 'first_name', 'last_name', 'is_staff', 'password')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Parolni hash qilish (MUHIM!)
        if commit:
            user.save()
        return user