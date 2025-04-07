from django.conf import settings


def get_user_agent(task: str) -> str:
    return settings.USER_AGENT_BASE.format(task)