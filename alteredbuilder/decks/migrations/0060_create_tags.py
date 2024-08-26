from django.db import migrations


def init_models(apps):
    global Tag
    Tag = apps.get_model("decks", "Tag")


def delete_tags(apps, schema_editor):
    init_models(apps)

    Tag.objects.all().delete()


def create_tags(apps, schema_editor):
    init_models(apps)

    tags = []
    data = [
        {
            "name": "Aggro",
            "type": "TY",
            "description_en": "Get an early lead and maintain pressure.",
            "description_es": "",
            "description_fr": "",
            "description_it": "",
            "description_de": "",
        },
        {
            "name": "Midrange",
            "type": "TY",
            "description_en": "Balance early aggression with late-game stability.",
            "description_es": "",
            "description_fr": "",
            "description_it": "",
            "description_de": "",
        },
        {
            "name": "Control",
            "type": "TY",
            "description_en": "Aims to prolong the game and gain control for a late win.",
            "description_es": "Busca prolongar el juego y ganar control para una victoria tardía.",
            "description_fr": "Vise à prolonger la partie et à prendre le contrôle pour une victoire tardive.",
            "description_it": "Mira a prolungare il gioco e ottenere il controllo per una vittoria tardiva.",
            "description_de": "Zielt darauf ab, das Spiel zu verlängern und die Kontrolle zu übernehmen, um spät zu gewinnen.",
        },
        {
            "name": "Combo",
            "type": "SU",
            "description_en": "Uses card combinations to achieve powerful effects.",
            "description_es": "Utiliza combinaciones de cartas para lograr efectos poderosos.",
            "description_fr": "Utilise des combinaisons de cartes pour obtenir des effets puissants.",
            "description_it": "Utilizza combinazioni di carte per ottenere effetti potenti.",
            "description_de": "Nutzt Kartenkombinationen, um mächtige Effekte zu erzielen.",
        },
        {
            "name": "Token",
            "type": "SU",
            "description_en": "Focuses on generating and utilizing token creatures.",
            "description_es": "Se centra en generar y utilizar criaturas de fichas.",
            "description_fr": "Se concentre sur la génération et l'utilisation de créatures jetons.",
            "description_it": "Si concentra sulla generazione e sull'utilizzo di creature token.",
            "description_de": "Konzentriert sich auf die Erzeugung und Nutzung von Token-Kreaturen.",
        },
        {
            "name": "Disruption",
            "type": "SU",
            "description_en": "Interferes with the opponent's strategy and resources.",
            "description_es": "Interfiere con la estrategia y los recursos del oponente.",
            "description_fr": "Interfère avec la stratégie et les ressources de l'adversaire.",
            "description_it": "Interferisce con la strategia e le risorse dell'avversario.",
            "description_de": "Stört die Strategie und Ressourcen des Gegners.",
        },
        {
            "name": "Ramp",
            "type": "SU",
            "description_en": "Increases resources to play big cards faster.",
            "description_es": "Aumenta los recursos para jugar cartas grandes más rápido.",
            "description_fr": "Augmente les ressources pour jouer des grandes cartes plus rapidement.",
            "description_it": "Aumenta le risorse per giocare carte grandi più velocemente.",
            "description_de": "Erhöht Ressourcen, um größere Karten schneller zu spielen.",
        },
    ]

    for tag_data in data:

        tags.append(Tag(**tag_data))

    Tag.objects.bulk_create(tags)


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0059_tag_deck_tags"),
    ]

    operations = [
        migrations.RunPython(code=create_tags, reverse_code=delete_tags),
    ]
