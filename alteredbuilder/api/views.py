from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from . import serializers as serial
from decks.models import Card


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited by admins
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = serial.UserSerializer
    permission_classes = [permissions.IsAdminUser]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited by admins
    """

    queryset = Group.objects.all()
    serializer_class = serial.GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminWriteOrAuthenticatedGetViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class CardViewSet(AdminWriteOrAuthenticatedGetViewSet):
    """API endpoint that allows to view all the cards."""

    queryset = Card.objects.all().order_by("reference")
    serializer_class = serial.CardSerializer

    def retrieve(self, request: Request, pk=None) -> Response:
        """Retrieve the information of a card.

        Args:
            request (Request): Request object.
            pk (str, optional): Primary key of the object to retrieve. Defaults to None.

        Returns:
            Response: The Card's full data.
        """
        card = get_object_or_404(Card, pk=pk)
        context = {"request": request}
        serializer = serial.CardSerializer(card, context=context)

        return Response(serializer.data)
