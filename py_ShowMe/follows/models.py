# follows/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)  # For private profiles
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} → {self.following.username} ({'Accepted' if self.accepted else 'Pending'})"
