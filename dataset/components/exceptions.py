# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from abc import ABCMeta
from abc import abstractmethod
from http.client import CONFLICT
from http.client import FORBIDDEN
from http.client import INTERNAL_SERVER_ERROR
from http.client import NOT_FOUND
from http.client import UNAUTHORIZED
from typing import Dict


class ServiceException(Exception, metaclass=ABCMeta):
    """Base class for service exceptions."""

    domain: str = 'global'

    @property
    @abstractmethod
    def status(self) -> int:
        """HTTP status code applicable to the problem."""

        raise NotImplementedError

    @property
    @abstractmethod
    def code(self) -> str:
        """Component-specific error code."""

        raise NotImplementedError

    @property
    @abstractmethod
    def details(self) -> str:
        """Additional information with specific explanation for this occurrence of the problem."""

        raise NotImplementedError

    def dict(self) -> Dict[str, str]:
        """Represent error as dictionary."""

        return {
            'code': f'{self.domain}.{self.code}',
            'details': self.details,
        }


class UnhandledException(ServiceException):
    """Raised when unhandled/unexpected internal error occurred."""

    @property
    def status(self) -> int:
        return INTERNAL_SERVER_ERROR

    @property
    def code(self) -> str:
        return 'unhandled_exception'

    @property
    def details(self) -> str:
        return 'Unexpected Internal Server Error'


class NotFound(ServiceException):
    """Raised when requested resource is not found."""

    @property
    def status(self) -> int:
        return NOT_FOUND

    @property
    def code(self) -> str:
        return 'not_found'

    @property
    def details(self) -> str:
        return 'Requested resource is not found'


class AlreadyExists(ServiceException):
    """Raised when target resource already exists."""

    @property
    def status(self) -> int:
        return CONFLICT

    @property
    def code(self) -> str:
        return 'already_exists'

    @property
    def details(self) -> str:
        return 'Target resource already exists'


class Forbidden(ServiceException):
    """Raised when target resource already exists."""

    @property
    def status(self) -> int:
        return FORBIDDEN

    @property
    def code(self) -> str:
        return 'forbidden'

    @property
    def details(self) -> str:
        return 'Operation not allowed '


class Unauthorized(ServiceException):
    """Raised when user authorization fails for a given resource."""

    @property
    def status(self) -> int:
        return UNAUTHORIZED

    @property
    def code(self) -> str:
        return 'unauthorized'

    @property
    def details(self) -> str:
        return 'Unauthorized access to requested resource'
