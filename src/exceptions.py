from fastapi import HTTPException


class TestException(Exception):
    detail = "Неожиданная ошибка"

    def __init__(self, *args, **kwargs):
        super().__init__(self.detail, *args, **kwargs)


class ObjectNotFoundException(TestException):
    detail = "Объект не найден"


class ToShortPasswordValueErrorException(TestException):
    detail = "Пароль должен быть не менее восьми символов"


class ObjectAlreadyExistsException(TestException):
    detail = "Похожий объект уже существует"


class UserDeleteTokenException(TestException):
    detail = "Вы уже вышли из аккаунта"


class UserAllReadyExistsException(TestException):
    detail = "Пользователь с таким email уже зарегистрирован"


class UserNotRegisterException(TestException):
    detail = "Пользователь с таким email не зарегистрирован"


class WrongPasswordException(TestException):
    detail = "Неверный пароль"


class AdminOnlyAccessException(TestException):
    detail = "Доступ только для администратора"


# === HTTP-исключения (для ответа клиенту) ===
class TestHTTPException(HTTPException):
    status_code = 500
    detail = None

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class UserDeleteTokenHTTPException(TestHTTPException):
    status_code = 401
    detail = "Вы уже вышли из аккаунта"


class UserPasswordToShortHTTPException(TestHTTPException):
    status_code = 422
    detail = "Пароль должен содержать минимум 8 символов"


class UserAllReadyExistsHTTPException(TestHTTPException):
    status_code = 409
    detail = "Пользователь с таким email уже зарегистрирован"


class UserNotRegisterHTTPException(TestHTTPException):
    status_code = 401
    detail = "Пользователь с таким email не зарегистрирован"


class UserIndexWrongHTTPException(TestHTTPException):
    status_code = 422
    detail = "Индекс не может быть меньше или равным нулю"


class UserNotFoundHTTPException(TestHTTPException):
    status_code = 404
    detail = "Пользователь не существует"


class WrongPasswordHTTPException(TestHTTPException):
    status_code = 401
    detail = "Неверный пароль"


class AdminOnlyAccessHTTPException(TestHTTPException):
    status_code = 403
    detail = "Доступ только для администратора"

class AdminOrManagerOnlyAccessHTTPException(TestHTTPException):
    status_code = 403
    detail = "Доступ только для администратора или менеджера"


class DeactivateUserHTTPException(TestHTTPException):
    status_code = 403
    detail = "Аккаунт деактивирован. Обратитесь к администратору."


class TokenWrongTypeHTTPException(TestHTTPException):
    status_code = 401
    detail = "Неверный тип токена"


class ExpiredSignatureErrorHTTPException(TestHTTPException):
    status_code = 401
    detail = "Токен истек"


class PyJWTErrorHTTPException(TestHTTPException):
    status_code = 401
    detail = "Неверный JWT-токен"


class RefreshTokenRequiredHTTPException(TestHTTPException):
    status_code = 401
    detail = "Требуется рефреш токен"


class WrongRefreshTokenHTTPException(TestHTTPException):
    status_code = 401
    detail = "Неверный рефреш токен"


class WrongUserDataHTTPException(TestHTTPException):
    status_code = 401
    detail = "Неудалось получить данные пользователя"
