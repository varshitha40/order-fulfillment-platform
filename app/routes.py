from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Order, Inventory, Shipment

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template(
        "index.html",
        total_orders=Order.query.count(),
        pending_orders=Order.query.filter_by(status="Pending").count(),
        total_products=Inventory.query.count(),
        shipments=Shipment.query.count()
    )


@main.route("/orders")
def orders():
    all_orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("orders.html", orders=all_orders)


@main.route("/inventory")
def inventory():
    products = Inventory.query.order_by(Inventory.product_name).all()
    return render_template("inventory.html", products=products)


@main.route("/shipping")
def shipping():
    all_shipments = Shipment.query.order_by(Shipment.id.desc()).all()
    return render_template("shipping.html", shipments=all_shipments)


@main.route("/tracking", methods=["GET", "POST"])
def tracking():
    shipment = None

    if request.method == "POST":
        tracking_number = request.form.get("tracking_number", "").strip()
        shipment = Shipment.query.filter_by(
            tracking_number=tracking_number
        ).first()

        if not shipment:
            flash("Tracking number not found.", "error")

    return render_template("tracking.html", shipment=shipment)


@main.route("/add-order", methods=["GET", "POST"])
def add_order():
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        product_name = request.form.get("product_name", "").strip()
        address = request.form.get("address", "").strip()

        try:
            quantity = int(request.form.get("quantity", "0"))
        except ValueError:
            quantity = 0

        if not customer_name or not product_name or not address or quantity < 1:
            flash("Enter valid order details.", "error")
            return redirect(url_for("main.add_order"))

        product = Inventory.query.filter_by(
            product_name=product_name
        ).first()

        if not product or product.quantity - product.allocated < quantity:
            flash("Product is unavailable or stock is insufficient.", "error")
            return redirect(url_for("main.add_order"))

        order = Order(
            customer_name=customer_name,
            product_name=product_name,
            quantity=quantity,
            address=address,
            status="Processing"
        )

        product.allocated += quantity
        db.session.add(order)
        db.session.commit()

        flash("Order created successfully!", "success")
        return redirect(url_for("main.orders"))

    products = Inventory.query.filter(
        Inventory.quantity > Inventory.allocated
    ).order_by(Inventory.product_name).all()

    return render_template("add_order.html", products=products)


@main.route("/add-inventory", methods=["POST"])
def add_inventory():
    product_name = request.form.get("product_name", "").strip()

    try:
        quantity = int(request.form.get("quantity", "-1"))
    except ValueError:
        quantity = -1

    if not product_name or quantity < 0:
        flash("Enter a valid product and quantity.", "error")
        return redirect(url_for("main.inventory"))

    product = Inventory.query.filter_by(product_name=product_name).first()

    if product:
        product.quantity += quantity
    else:
        product = Inventory(product_name=product_name, quantity=quantity)
        db.session.add(product)

    db.session.commit()
    flash("Inventory updated successfully!", "success")
    return redirect(url_for("main.inventory"))


@main.route("/create-shipment/<int:order_id>", methods=["POST"])
def create_shipment(order_id):
    order = db.get_or_404(Order, order_id)

    existing = Shipment.query.filter_by(order_id=order.id).first()
    if existing:
        flash("Shipment already exists for this order.", "error")
        return redirect(url_for("main.orders"))

    courier = request.form.get("courier", "").strip()
    if not courier:
        flash("Enter a courier name.", "error")
        return redirect(url_for("main.orders"))

    shipment = Shipment(
        order_id=order.id,
        courier=courier,
        tracking_number=f"TRK{order.id:05d}",
        status="Shipped"
    )

    order.status = "Shipped"
    db.session.add(shipment)
    db.session.commit()

    flash(f"Shipment created! Tracking number: {shipment.tracking_number}", "success")
    return redirect(url_for("main.shipping"))


@main.route("/update-shipment/<int:shipment_id>", methods=["POST"])
def update_shipment(shipment_id):
    shipment = db.get_or_404(Shipment, shipment_id)
    status = request.form.get("status", "")

    allowed = [
        "Preparing", "Shipped", "In Transit",
        "Out for Delivery", "Delivered"
    ]

    if status not in allowed:
        flash("Invalid shipment status.", "error")
        return redirect(url_for("main.shipping"))

    shipment.status = status
    shipment.order.status = status if status != "Preparing" else "Processing"

    db.session.commit()
    flash("Shipment status updated successfully!", "success")
    return redirect(url_for("main.shipping"))