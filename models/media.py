"""
Media model
"""
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Media(Base):
    __tablename__ = 'media'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    folder_id = Column(BigInteger, ForeignKey('folders.id', ondelete='CASCADE'), nullable=False)
    telegram_file_id = Column(String(255), nullable=False, index=True)
    file_unique_id = Column(String(255), nullable=False)
    media_type = Column(String(50), nullable=False)  # 'photo' or 'video'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    folder = relationship('Folder', back_populates='media')
    
    # Indexes
    __table_args__ = (
        Index('ix_media_folder_id', 'folder_id'),
        Index('ix_media_type', 'media_type'),
    )
    
    def __repr__(self):
        return f"<Media(id={self.id}, type={self.media_type}, folder_id={self.folder_id})>"
