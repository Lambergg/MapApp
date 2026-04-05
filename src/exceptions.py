from fastapi import HTTPException


class MapAppException(Exception):
    detail = "Неожиданная ошибка"

    def __init__(self, *args, **kwargs):
        super().__init__(self.detail, *args, **kwargs)


class ObjectNotFoundException(MapAppException):
    detail = "Объект не найден"


class ToShortPasswordValueErrorException(MapAppException):
    detail = "Пароль должен быть не менее восьми символов"


class ObjectAlreadyExistsException(MapAppException):
    detail = "Похожий объект уже существует"


class UserDeleteTokenException(MapAppException):
    detail = "Вы уже вышли из аккаунта"


class UserAllReadyExistsException(MapAppException):
    detail = "Пользователь с таким email уже зарегистрирован"


class UserNotRegisterException(MapAppException):
    detail = "Пользователь с таким email не зарегистрирован"


class WrongPasswordException(MapAppException):
    detail = "Неверный пароль"


class AdminOnlyAccessException(MapAppException):
    detail = "Доступ только для администратора"


# === HTTP-исключения (для ответа клиенту) ===
class MapAppHTTPException(HTTPException):
    status_code = 500
    detail = None

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class UserDeleteTokenHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Вы уже вышли из аккаунта"


class UserPasswordToShortHTTPException(MapAppHTTPException):
    status_code = 422
    detail = "Пароль должен содержать минимум 8 символов"


class UserAllReadyExistsHTTPException(MapAppHTTPException):
    status_code = 409
    detail = "Пользователь с таким email уже зарегистрирован"


class UserNotRegisterHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Пользователь с таким email не зарегистрирован"


class UserIndexWrongHTTPException(MapAppHTTPException):
    status_code = 422
    detail = "Индекс не может быть меньше или равным нулю"


class UserNotFoundHTTPException(MapAppHTTPException):
    status_code = 404
    detail = "Пользователь не существует"


class WrongPasswordHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Неверный пароль"


class AdminOnlyAccessHTTPException(MapAppHTTPException):
    status_code = 403
    detail = "Доступ только для администратора"

class AdminOrManagerOnlyAccessHTTPException(MapAppHTTPException):
    status_code = 403
    detail = "Доступ только для администратора или менеджера"


class DeactivateUserHTTPException(MapAppHTTPException):
    status_code = 403
    detail = "Аккаунт деактивирован. Обратитесь к администратору."


class TokenWrongTypeHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Неверный тип токена"


class ExpiredSignatureErrorHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Токен истек"


class PyJWTErrorHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Неверный JWT-токен"


class RefreshTokenRequiredHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Требуется рефреш токен"


class WrongRefreshTokenHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Неверный рефреш токен"


class WrongUserDataHTTPException(MapAppHTTPException):
    status_code = 401
    detail = "Неудалось получить данные пользователя"
