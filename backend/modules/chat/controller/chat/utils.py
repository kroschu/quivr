import time
from uuid import UUID

from fastapi import HTTPException
from logger import get_logger
from models import UserUsage
from modules.user.entity.user_identity import UserIdentity

logger = get_logger(__name__)


class NullableUUID(UUID):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v) -> UUID | None:
        if v == "":
            return None
        try:
            return UUID(v)
        except ValueError:
            return None


def check_user_requests_limit(user: UserIdentity, model: str):
    # TODO : Pass objects to avoid multiple calls to the database
    """Checks the user requests limit.
    It checks the user requests limit and raises an exception if the user has reached the limit.
    By default, the user has a limit of 100 requests per month. The limit can be increased by upgrading the plan.

    Args:
        user (UserIdentity): User object
        model (str): Model name for which the user is making the request

    Raises:
        HTTPException: Raises a 429 error if the user has reached the limit.
    """
    userDailyUsage = UserUsage(id=user.id, email=user.email)

    userSettings = userDailyUsage.get_user_settings()

    date = time.strftime("%Y%m%d")

    monthly_chat_credit = userSettings.get("monthly_chat_credit", 100)
    daily_user_count = userDailyUsage.get_user_monthly_usage(date)
    models_price = userDailyUsage.get_model_settings()
    user_choosen_model_price = 1000

    for model_setting in models_price:
        if model_setting["name"] == model:
            user_choosen_model_price = model_setting["price"]

    if int(daily_user_count + user_choosen_model_price) > int(monthly_chat_credit):
        raise HTTPException(
            status_code=429,  # pyright: ignore reportPrivateUsage=none
            detail=f"You have reached your monthly chat limit of {monthly_chat_credit} requests per months. Please upgrade your plan to increase your daily chat limit.",
        )
    else:
        userDailyUsage.handle_increment_user_request_count(
            date, user_choosen_model_price
        )
        pass
