from django.db import models
from django.contrib.auth.models import User

class Group(models.Model):
    ip_address = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  # 追加

    def __str__(self):
        return self.ip_address

class GroupCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    code = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f'{self.user.username} - {self.group.ip_address}'

class UserGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} in {self.group.ip_address}'