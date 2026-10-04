"""
Folder model
"""
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='folders')
    media = relationship('Media', back_populates='folder', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_folder_name'),
        Index('ix_folders_user_id', 'user_id'),
    )
    
    def __repr__(self):
        return f"<Folder(id={self.id}, name={self.name}, user_id={self.user_id})>"
