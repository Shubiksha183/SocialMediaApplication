from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Friendship
from .serializers import FriendshipSerializer
from django.db import models
from userProfile.models import Profile 

User = get_user_model()

class SendFriendRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        sender = request.user
        receiver = get_object_or_404(User, id=user_id)

        if sender == receiver:
            return Response({"message": "You cannot send a friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Already sent or reverse request exists
        if Friendship.objects.filter(sender=sender, receiver=receiver).exists() or Friendship.objects.filter(sender=receiver, receiver=sender).exists():
            return Response({"message": "Friend request already exists or you are already friends."}, status=status.HTTP_400_BAD_REQUEST)

        # Get receiver's privacy status
        try:
            receiver_profile = receiver.profile  # related name for OneToOneField is `profile`
        except Profile.DoesNotExist:
            return Response({"message": "Receiver's profile not found."}, status=status.HTTP_404_NOT_FOUND)

        if receiver_profile.privacy == 'public':
            # Directly create accepted friendship
            Friendship.objects.create(sender=sender, receiver=receiver, accepted=True)
            return Response({"message": "You are now friends."}, status=status.HTTP_201_CREATED)
        else:
            # Private profile → create pending friend request
            Friendship.objects.create(sender=sender, receiver=receiver, accepted=False)
            return Response({"message": "Friend request sent. Awaiting acceptance."}, status=status.HTTP_201_CREATED)




class AcceptFriendRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        friendship = get_object_or_404(Friendship, id=request_id, receiver=request.user)
        friendship.accepted = True
        friendship.save()

        # Optional: Remove duplicate reverse pending request if exists
        reverse = Friendship.objects.filter(sender=request.user, receiver=friendship.sender, accepted=False).first()
        if reverse:
            reverse.delete()

        return Response({"message": "Friend request accepted"}, status=status.HTTP_200_OK)



class FriendList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        friends = User.objects.filter(
            id__in=Friendship.objects.filter(accepted=True, sender=user).values_list('receiver', flat=True)
        ) | User.objects.filter(
            id__in=Friendship.objects.filter(accepted=True, receiver=user).values_list('sender', flat=True)
        )

        pending_requests_received = Friendship.objects.filter(receiver=user, accepted=False)
        pending_requests_sent = Friendship.objects.filter(sender=user, accepted=False)

        return Response({
            "friends": [{"id": friend.id, "username": friend.username} for friend in friends],
            "pending_requests_received": [{"id": req.id, "sender": req.sender.username} for req in pending_requests_received],
            "pending_requests_sent": [{"id": req.id, "receiver": req.receiver.username} for req in pending_requests_sent],
        }, status=status.HTTP_200_OK)

class UnfollowFriend(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        user = request.user

        # Check for friendship in either direction
        friendship = Friendship.objects.filter(
            accepted=True
        ).filter(
            (models.Q(sender=user, receiver__id=user_id)) | (models.Q(sender__id=user_id, receiver=user))
        ).first()

        if not friendship:
            return Response({"message": "Friendship not found."}, status=status.HTTP_404_NOT_FOUND)

        friendship.delete()
        return Response({"message": "Unfollowed (unfriended) successfully."}, status=status.HTTP_200_OK)

class CancelFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, receiver_id):
        try:
            friend_request = Friendship.objects.get(sender=request.user, receiver_id=receiver_id, accepted=False)
            friend_request.delete()
            return Response({"detail": "Friend request cancelled."}, status=status.HTTP_204_NO_CONTENT)
        except Friendship.DoesNotExist:
            return Response({"detail": "No pending friend request to cancel."}, status=status.HTTP_404_NOT_FOUND)