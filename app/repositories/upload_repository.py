from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Upload


class UploadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, upload_id: str) -> Upload | None:
        return self.db.get(Upload, upload_id)

    def list_all(self) -> list[Upload]:
        return list(self.db.scalars(select(Upload)))

    def list_by_empresa(self, empresa_id: str) -> list[Upload]:
        return list(self.db.scalars(select(Upload).where(Upload.empresa_id == empresa_id)))

    def count(self) -> int:
        return self.db.query(Upload).count()

    def create(self, upload: Upload) -> Upload:
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        return upload

    def update(self, upload: Upload) -> Upload:
        self.db.commit()
        self.db.refresh(upload)
        return upload
