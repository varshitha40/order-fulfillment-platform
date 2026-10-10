
from app import db
from datetime import datetime


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    allocated = db.Column(db.Integer, default=0)


class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id"), nullable=False
    )
    courier = db.Column(db.String(100), default="Not assigned")
    tracking_number = db.Column(db.String(100), unique=True, nullable=True)
    status = db.Column(db.String(50), default="Preparing")

    order = db.relationship("Order", backref="shipments")
