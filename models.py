from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


Base = declarative_base()

class Brand(Base):
    __tablename__ = 'brand'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True)
    sourceUrl = Column(String(256))
    createdAt = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current time at insertion
    updatedAt = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current time at insertion and update


    # Relationship to products (one-to-many)
    products = relationship("Product", back_populates="brand")

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    brandId = Column(Integer, ForeignKey('brand.id'))
    url = Column(String(255), nullable=False)
    genderId = Column(Integer, ForeignKey('gender.id'))
    retailerId = Column(Integer, nullable=False)
    originalProductId = Column(String(255))
    createdAt = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current time at insertion
    updatedAt = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current time at insertion and update


    # Relationships
    brand = relationship("Brand", back_populates="products")
    gender = relationship("Gender", back_populates="products")
    categories = relationship("ProductHasCategory", back_populates="product")
    images = relationship("ProductImage", back_populates="product")


class Gender(Base):
    __tablename__ = 'gender'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    prettyName = Column(String(100), nullable=False)
    description = Column(String(2000), nullable=False)
    createdAt = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current time at insertion
    updatedAt = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current time at insertion and update


    # Relationship back to Product
    products = relationship("Product", back_populates="gender")

class ProductCategory(Base):
    __tablename__ = 'productcategory'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    createdAt = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current time at insertion
    updatedAt = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current time at insertion and update


    # Relationship definition for bidirectional access between Product and ProductCategory
    products = relationship("ProductHasCategory", back_populates="category")


class ProductHasCategory(Base):
    __tablename__ = 'producthascategory'
    id = Column(Integer, primary_key=True)
    productId = Column(Integer, ForeignKey('product.id'))
    categoryId = Column(Integer, ForeignKey('productcategory.id'))
    categoryLevel = Column(Integer, default=1)

    # Relationships to enable navigation from the join table to Product and ProductCategory
    product = relationship("Product", back_populates="categories")
    category = relationship("ProductCategory", back_populates="products")
    createdAt = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current time at insertion
    updatedAt = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current time at insertion and update



class Color(Base):
    __tablename__ = 'color'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    createdAt = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current time at insertion
    updatedAt = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current time at insertion and update

    images = relationship("ProductImage", back_populates="color")


class ProductImage(Base):
    __tablename__ = 'productimage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey('product.id'), nullable=False)
    colorId = Column(Integer, ForeignKey('color.id'), nullable=True)
    prices = Column(JSON, nullable=False)
    originalImages = Column(JSON, nullable=True)
    reuploadedImages = Column(JSON, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="images")
    color = relationship("Color", back_populates="images")
