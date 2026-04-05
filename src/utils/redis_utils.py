from src.init import redis_manager_auth


async def delete_refresh_token(user_id: int):
    old_refresh_token = await redis_manager_auth.get(f"refresh_token:{user_id}")
    if not old_refresh_token:
        return

    await redis_manager_auth.delete(f"rt:{old_refresh_token}")
    await redis_manager_auth.delete(f"refresh_token:{user_id}")
    await redis_manager_auth.delete(f"user_role:{user_id}")
