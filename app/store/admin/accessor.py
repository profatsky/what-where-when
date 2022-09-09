from sqlalchemy import select

from app.admin.models import Admin, AdminModel
from app.base.base_accessor import BaseAccessor


class AdminAccessor(BaseAccessor):
    async def get_by_email(self, email: str) -> Admin | None:
        async with self.app.database.session() as session:
            result = await session.execute(
                select(AdminModel)
                .where(AdminModel.email == email)
            )
        obj: AdminModel | None = result.scalar()
        if obj is None:
            return

        return obj.to_dc()

    async def create_admin(self, email: str, password: str) -> Admin:
        new_admin = AdminModel(email=email, password=password)
        async with self.app.database.session.begin() as session:
            session.add(new_admin)
        return new_admin.to_dc()
