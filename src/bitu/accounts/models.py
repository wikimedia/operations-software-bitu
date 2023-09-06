# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


@dataclass
class EmailUpdate:
    user: User
    email: str