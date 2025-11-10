from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from werkzeug.security import generate_password_hash, check_password_hash # تم تصحيح هذا السطر
import datetime, uuid


# --- إعداد الاتصال بقاعدة البيانات ---
# سيتم الآن تكوين هذه المتغيرات ديناميكياً عند بدء التشغيل
engine = None
SessionLocal = None
Base = declarative_base()

def setup_database_connection(db_url):
    """يقوم بإعداد محرك قاعدة البيانات وجلسة الاتصال بناءً على الرابط المقدم"""
    global engine, SessionLocal
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

# --- تعريف الجداول ---

class Item(Base):
    """
    يمثل هذا الكلاس جدول الأصناف (items) في قاعدة البيانات.
    """
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"))
    store = relationship("Store")
    quantity = Column(Integer, default=0)
    cost_price = Column(Float, default=0.0)
    sale_price = Column(Float, default=0.0)
    image_path = Column(String, nullable=True)

    def __repr__(self):
        return f"<Item(name='{self.name}', code='{self.code}')>"

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String) # حقل إضافي لموقع المخزن مثلاً

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    phone = Column(String)
    address = Column(String)
    current_balance = Column(Float, default=0.0) # الرصيد المستحق لنا أو لهم

    purchase_invoices = relationship("PurchaseInvoice", back_populates="supplier")
    purchase_returns = relationship("PurchaseReturn", back_populates="supplier")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    phone = Column(String)
    address = Column(String)
    email = Column(String, unique=True, nullable=True) # <-- الحقل الجديد
    current_debt = Column(Float, default=0.0)
    
    invoices = relationship("Invoice", back_populates="customer")
    sales_returns = relationship("SalesReturn", back_populates="customer") # <-- إضافة علاقة مرتجعات المبيعات

class Seller(Base):
    __tablename__ = "sellers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    phone = Column(String)
    address = Column(String)
    
    invoices = relationship("Invoice", back_populates="seller")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=True)
    date = Column(Date, default=datetime.date.today)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    payment_method = Column(String, default="نقدي") # <-- إضافة حقل طريقة الدفع
    is_draft = Column(Integer, default=0) # 0 for approved, 1 for draft
    notes = Column(String, nullable=True)
    discount_amount = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)

    customer = relationship("Customer", back_populates="invoices")
    seller = relationship("Seller", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer)
    price_per_unit = Column(Float)
    discount_percent = Column(Float, default=0.0)

    invoice = relationship("Invoice", back_populates="items")
    item = relationship("Item")

class SalesReturn(Base):
    __tablename__ = "sales_returns"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    date = Column(Date, default=datetime.date.today)
    total_amount = Column(Float, default=0.0)
    refund_amount = Column(Float, default=0.0) # المبلغ المسترجع للعميل
    notes = Column(String, nullable=True)

    customer = relationship("Customer", back_populates="sales_returns")
    items = relationship("SalesReturnItem", back_populates="sales_return")

class SalesReturnItem(Base):
    __tablename__ = "sales_return_items"
    id = Column(Integer, primary_key=True, index=True)
    sales_return_id = Column(Integer, ForeignKey("sales_returns.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer)
    price_per_unit = Column(Float)

    sales_return = relationship("SalesReturn", back_populates="items")
    item = relationship("Item")

class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    date = Column(Date, default=datetime.date.today)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    payment_method = Column(String, default="نقدي")

    supplier = relationship("Supplier", back_populates="purchase_invoices")
    items = relationship("PurchaseInvoiceItem", back_populates="purchase_invoice")

class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer)
    price_per_unit = Column(Float) # سعر الشراء

    purchase_invoice = relationship("PurchaseInvoice", back_populates="items")
    item = relationship("Item")

class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    date = Column(Date, default=datetime.date.today)
    total_amount = Column(Float, default=0.0)
    received_amount = Column(Float, default=0.0) # المبلغ المستلم من المورد
    notes = Column(String, nullable=True)

    supplier = relationship("Supplier", back_populates="purchase_returns")
    items = relationship("PurchaseReturnItem", back_populates="purchase_return")

class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_return_id = Column(Integer, ForeignKey("purchase_returns.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer)
    price_per_unit = Column(Float)

    purchase_return = relationship("PurchaseReturn", back_populates="items")
    item = relationship("Item")

class TreasuryTransaction(Base):
    __tablename__ = "treasury_transactions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=datetime.date.today)
    transaction_type = Column(String, nullable=False) # 'إيداع' أو 'سحب'
    amount = Column(Float, nullable=False)
    description = Column(String)
    current_balance = Column(Float, nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    invoice = relationship("Invoice")
    customer = relationship("Customer")
    supplier = relationship("Supplier")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Activation(Base):
    __tablename__ = "activation"
    id = Column(Integer, primary_key=True)
    serial_key = Column(String, unique=True, nullable=False)
    activation_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    subscription_type = Column(String, nullable=False) # 'trial', 'monthly', or 'yearly'


def _run_migrations(engine):
    """
    يقوم بتشغيل تحديثات بسيطة على هيكل قاعدة البيانات.
    هذا يضمن أن الأعمدة الجديدة تضاف إلى الجداول الموجودة.
    """
    inspector = inspect(engine)
    with engine.connect() as connection:
        with connection.begin() as trans: # استخدام transaction لضمان تنفيذ كل التغييرات معًا
            # --- Migrations for 'invoices' table ---
            invoice_columns = [col['name'] for col in inspector.get_columns('invoices')]
            if 'seller_id' not in invoice_columns:
                print("Running migration: Adding 'seller_id' to 'invoices' table...")
                connection.execute(text('ALTER TABLE invoices ADD COLUMN seller_id INTEGER REFERENCES sellers(id)'))
            if 'notes' not in invoice_columns:
                print("Running migration: Adding 'notes' to 'invoices' table...")
                connection.execute(text('ALTER TABLE invoices ADD COLUMN notes VARCHAR'))
            if 'discount_amount' not in invoice_columns:
                print("Running migration: Adding 'discount_amount' to 'invoices' table...")
                connection.execute(text('ALTER TABLE invoices ADD COLUMN discount_amount FLOAT'))
            if 'tax_rate' not in invoice_columns:
                print("Running migration: Adding 'tax_rate' to 'invoices' table...")
                connection.execute(text('ALTER TABLE invoices ADD COLUMN tax_rate FLOAT'))

            # --- Migrations for 'invoice_items' table ---
            invoice_item_columns = [col['name'] for col in inspector.get_columns('invoice_items')]
            if 'discount_percent' not in invoice_item_columns:
                print("Running migration: Adding 'discount_percent' to 'invoice_items' table...")
                connection.execute(text('ALTER TABLE invoice_items ADD COLUMN discount_percent FLOAT'))

            # --- Migrations for 'customers' table ---
            customer_columns = [col['name'] for col in inspector.get_columns('customers')]
            if 'email' not in customer_columns:
                print("Running migration: Adding 'email' to 'customers' table...")
                connection.execute(text('ALTER TABLE customers ADD COLUMN email VARCHAR'))

            # التحقق من وجود الفهرس الفريد على عمود email
            customer_indexes = [idx['name'] for idx in inspector.get_indexes('customers')]
            if 'ix_customers_email_unique' not in customer_indexes:
                print("Running migration: Adding UNIQUE constraint to 'customers.email'...")
                # SQLite requires a separate command to create an index
                if 'sqlite' in engine.dialect.name:
                    try:
                        connection.execute(text('CREATE UNIQUE INDEX ix_customers_email_unique ON customers (email)'))
                    except Exception as e:
                        # This might fail if there are duplicate NULLs, which is fine.
                        print(f"Could not create unique index on email, possibly due to existing data: {e}")
                else:
                    # For other databases, we might try adding a unique constraint
                    # This is more complex and varies by DB, so we'll stick to the index
                    pass

            # --- Migrations for 'treasury_transactions' table ---
            treasury_columns = [col['name'] for col in inspector.get_columns('treasury_transactions')]
            if 'customer_id' not in treasury_columns:
                print("Running migration: Adding 'customer_id' to 'treasury_transactions' table...")
                connection.execute(text('ALTER TABLE treasury_transactions ADD COLUMN customer_id INTEGER REFERENCES customers(id)'))
            if 'supplier_id' not in treasury_columns:
                print("Running migration: Adding 'supplier_id' to 'treasury_transactions' table...")
                connection.execute(text('ALTER TABLE treasury_transactions ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id)'))





def init_db():
    """
    تقوم هذه الدالة بإنشاء جميع الجداول في قاعدة البيانات.
    يجب استدعاؤها مرة واحدة عند بدء تشغيل التطبيق.
    """
    if engine:
        # إنشاء جميع الجداول أولاً إذا لم تكن موجودة
        Base.metadata.create_all(bind=engine)

        # بعد ذلك، قم بتشغيل أي تحديثات ضرورية على هيكل الجداول
        _run_migrations(engine)

        # التحقق من وجود الجداول قبل إضافة المستخدم الافتراضي
        inspector = inspect(engine)
        
        # إضافة مستخدم افتراضي عند أول تشغيل
        session = SessionLocal()
        try: # تم تعديل هذا الجزء بالكامل
            if not session.query(User).first():
                admin_user = User(username="admin")
                admin_user.set_password("admin")
                session.add(admin_user)
                session.commit()

            # إضافة فترة تجريبية عند أول تشغيل للشركة إذا لم يكن هناك تفعيل
            if not session.query(Activation).first():
                today = datetime.date.today()
                expiry_date = today + datetime.timedelta(days=7)
                trial_activation = Activation(
                    serial_key=f"TRIAL-{uuid.uuid4()}", # سيريال فريد للفترة التجريبية
                    activation_date=today,
                    expiry_date=expiry_date,
                    subscription_type='trial'
                )
                session.add(trial_activation)
                session.commit()
        finally:
            session.close()