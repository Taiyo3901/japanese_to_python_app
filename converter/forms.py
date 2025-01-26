from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # フィールドのラベルを日本語に変更
        self.fields['username'].label = 'ユーザー名'
        self.fields['password1'].label = 'パスワード'
        self.fields['password2'].label = 'パスワード（確認用）'
        # ヘルプテキストを日本語に変更
        self.fields['username'].help_text = '必須。半角英数字、@/./+/-/_ が使えます。'
        self.fields['password1'].help_text = 'パスワードは8文字以上で、一般的すぎるパスワードや数字だけのパスワードは使用できません。'
        self.fields['password2'].help_text = '確認のため、再度パスワードを入力してください。'