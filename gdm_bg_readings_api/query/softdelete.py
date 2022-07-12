from typing import Any, Optional, Type

from flask_batteries_included.sqldb import db
from flask_sqlalchemy import BaseQuery


class QueryWithSoftDelete(BaseQuery):
    def __new__(cls, *args: Any, **kwargs: Any) -> "QueryWithSoftDelete":
        obj = super(QueryWithSoftDelete, cls).__new__(cls)
        with_deleted = kwargs.pop("_with_deleted", False)
        if len(args) > 0:
            super(QueryWithSoftDelete, obj).__init__(*args, **kwargs)
            return obj.filter_by(deleted=None) if not with_deleted else obj
        return obj

    def __init__(self, entities: Any, *args: Any, **kwargs: Any) -> None:
        # We're deliberately not calling the super init here.
        pass

    def with_deleted(self) -> Optional[Type["QueryWithSoftDelete"]]:
        return self.__class__(
            db.class_mapper(self._mapper_zero().class_),
            session=db.session(),
            _with_deleted=True,
        )
