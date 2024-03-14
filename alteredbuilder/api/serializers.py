from django.contrib.auth.models import Group, User
from rest_framework import serializers

from decks.models import Card, Character, Hero, Landmark, Spell


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class CardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Card
        fields = "__all__"


class CharacterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Character
        fields = "__all__"


class HeroSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Hero
        fields = "__all__"


class LandmarkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Landmark
        fields = "__all__"


class SpellSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Hero
        fields = "__all__"
