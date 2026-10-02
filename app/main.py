from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_engine, get_session
from app.models import Base
from app.payments import FakePaymentGateway, PaymentDeclinedError, PaymentGateway
from app.repository import SqlRepository
from app.services import InsufficientStockError, OrderService, ProductNotFoundError


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(get_engine())
    yield


app = FastAPI(title="Tienda DevOps - ejemplo de pruebas", lifespan=lifespan)
_gateway = FakePaymentGateway()


def get_payment_gateway() -> PaymentGateway:
    return _gateway


SessionDep = Annotated[Session, Depends(get_session)]
GatewayDep = Annotated[PaymentGateway, Depends(get_payment_gateway)]


class ProductIn(BaseModel):
    sku: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    price: Decimal = Field(ge=0, decimal_places=2)
    stock: int = Field(ge=0)


class ProductOut(ProductIn):
    id: int


class OrderItemIn(BaseModel):
    sku: str
    quantity: int = Field(gt=0)


class OrderIn(BaseModel):
    customer_type: str = "REGULAR"
    items: list[OrderItemIn] = Field(min_length=1)


class OrderOut(BaseModel):
    id: int
    subtotal: Decimal
    discount: Decimal
    igv: Decimal
    total: Decimal
    payment_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, session: SessionDep):
    repo = SqlRepository(session)
    try:
        product = repo.add_product(**data.model_dump())
        repo.commit()
    except IntegrityError:
        repo.rollback()
        raise HTTPException(409, f"El SKU {data.sku} ya existe") from None
    return ProductOut.model_validate(product, from_attributes=True)


@app.get("/products/{sku}", response_model=ProductOut)
def get_product(sku: str, session: SessionDep):
    product = SqlRepository(session).get_product(sku)
    if product is None:
        raise HTTPException(404, "Producto no encontrado")
    return ProductOut.model_validate(product, from_attributes=True)


@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(data: OrderIn, session: SessionDep, gateway: GatewayDep):
    service = OrderService(SqlRepository(session), gateway)
    try:
        order = service.place_order(
            data.customer_type, [(item.sku, item.quantity) for item in data.items]
        )
    except ProductNotFoundError as exc:
        raise HTTPException(404, f"Producto {exc} no existe") from None
    except InsufficientStockError as exc:
        raise HTTPException(409, f"Stock insuficiente para {exc}") from None
    except PaymentDeclinedError as exc:
        raise HTTPException(402, str(exc)) from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    return OrderOut.model_validate(order, from_attributes=True)
