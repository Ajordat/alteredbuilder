from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from . import serializers as serial
from decks.models import Card, Character, Hero, Landmark, Spell


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = serial.UserSerializer
    permission_classes = [permissions.IsAdminUser]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all()
    serializer_class = serial.GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all().order_by("reference")
    serializer_class = serial.CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, pk=None):
        card = get_object_or_404(Card, pk=pk)
        context = {"request": request}
        model, serializer = self.get_serializer_from_type(card.type)
        card = get_object_or_404(model, pk=pk)
        serializer = serializer(card, context=context)

        return Response(serializer.data)

    @staticmethod
    def get_serializer_from_type(card_type):
        try:
            return {
                Card.Type.CHARACTER: (Character, serial.CharacterSerializer),
                Card.Type.HERO: (Hero, serial.HeroSerializer),
                Card.Type.LANDMARK: (Landmark, serial.LandmarkSerializer),
                Card.Type.SPELL: (Spell, serial.SpellSerializer),
            }[card_type]
        except KeyError:
            return Card, serial.CardSerializer


class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.all().order_by("reference")
    serializer_class = serial.CharacterSerializer
    permission_classes = [permissions.IsAuthenticated]


class HeroViewSet(viewsets.ModelViewSet):
    queryset = Hero.objects.all().order_by("reference")
    serializer_class = serial.HeroSerializer
    permission_classes = [permissions.IsAuthenticated]


class LandmarkViewSet(viewsets.ModelViewSet):
    queryset = Landmark.objects.all().order_by("reference")
    serializer_class = serial.LandmarkSerializer
    permission_classes = [permissions.IsAuthenticated]


class SpellViewSet(viewsets.ModelViewSet):
    queryset = Spell.objects.all().order_by("reference")
    serializer_class = serial.SpellSerializer
    permission_classes = [permissions.IsAuthenticated]
