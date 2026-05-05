from src.init import redis_manager_auth


async def delete_refresh_token(user_id: int):
    """
    Удаляет refresh-токен и связанные с ним ключи из Redis.
    Выполняет очистку следующих ключей:
    - `refresh_token:{user_id}` — сам токен
    - `rt:{refresh_token}` — обратная ссылка на user_id
    - `user_role:{user_id}` — роль пользователя

    :param user_id: ID пользователя, чьи токены нужно удалить.
    :type user_id: int
    :return: Ничего не возвращает.
    :rtype: None
    """
    old_refresh_token = await redis_manager_auth.get(f"refresh_token:{user_id}")
    if not old_refresh_token:
        return

    await redis_manager_auth.delete(f"rt:{old_refresh_token}")
    await redis_manager_auth.delete(f"refresh_token:{user_id}")
    await redis_manager_auth.delete(f"user_role:{user_id}")
