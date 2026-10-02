"""Acceso a datos. Se prueba con pruebas de integración contra PostgreSQL real."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Order, Product


class SqlRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_product(self, sku: str, name: str, price, stock: int) -> Product:
        product = Product(sku=sku, name=name, price=price, stock=stock)
        self.session.add(product)
        self.session.flush()
        return product

    def get_product(self, sku: str) -> Product | None:
        return self.session.scalars(select(Product).where(Product.sku == sku)).first()

    def decrease_stock(self, sku: str, quantity: int) -> bool:
        """Descuenta stock de forma atómica. Devuelve False si no alcanza."""
        result = self.session.execute(
            update(Product)
            .where(Product.sku == sku, Product.stock >= quantity)
            .values(stock=Product.stock - quantity)
        )
        return result.rowcount == 1

    def save_order(self, order: Order) -> Order:
        self.session.add(order)
        self.session.flush()
        return order

    def get_order(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
