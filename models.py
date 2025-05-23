from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# User roles
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship('User', backref='role', lazy=True)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    profile_photo = db.Column(db.String(255), default='default_profile.svg')
    balance = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), default=2)  # Default to regular user
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    fund_requests = db.relationship('FundRequest', backref='user', lazy=True)
    fund_transactions = db.relationship('FundTransaction', backref='user', lazy=True)
    checked_items = db.relationship('CheckedItem', backref='user', lazy=True)
    post_comments = db.relationship('PostComment', backref='user', lazy=True)
    post_likes = db.relationship('PostLike', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_mail_user(self):
        return self.role_id == 3  # Assuming 3 is for 'mail' users
        
    def is_pass_user(self):
        return self.role_id == 4  # Assuming 4 is for 'pass' users
    
    def __repr__(self):
        return f'<User {self.username}>'

# Service categories
class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    services = db.relationship('Service', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'

# Services
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    rate = db.Column(db.Float, nullable=False)
    validity = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=False)
    items = db.relationship('StockItem', backref='service', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.name}>'

# Stock items
class StockItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    name = db.Column(db.String(100))
    mail = db.Column(db.String(100))
    password = db.Column(db.String(100))
    profile_link = db.Column(db.String(255))
    recovery_mail = db.Column(db.String(100))
    two_factor = db.Column(db.String(100))
    rate = db.Column(db.Float, nullable=False)
    is_checked = db.Column(db.Boolean, default=False)
    is_old = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StockItem {self.id} - {self.service.name}>'

# Checked items (links users to stock)
class CheckedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id'), nullable=False)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    stock_item = db.relationship('StockItem')
    
    def __repr__(self):
        return f'<CheckedItem User:{self.user_id} - Item:{self.stock_item_id}>'

# Fund Requests
class FundRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    is_received = db.Column(db.Boolean, default=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<FundRequest {self.id} - {self.amount} - {self.status}>'

# Fund Transactions
class FundTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # add, deduct
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FundTransaction {self.id} - {self.transaction_type} - {self.amount}>'

# Posts
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    photo_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    admin = db.relationship('User')
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.id} - {self.title}>'

# Post Comments
class PostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostComment {self.id} - Post:{self.post_id}>'

# Post Likes
class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostLike Post:{self.post_id} - User:{self.user_id}>'

# Website Settings
class WebsiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='Chief Elite BD')
    logo_url = db.Column(db.String(255), default='logo.svg')
    primary_color = db.Column(db.String(20), default='#007bff')
    secondary_color = db.Column(db.String(20), default='#6c757d')
    contact_phone = db.Column(db.String(20), default='01856659780')
    contact_email = db.Column(db.String(100))
    admin_notice = db.Column(db.Text)
    minimum_fund = db.Column(db.Float, default=20.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WebsiteSetting {self.site_name}>'

# Invoice Service Settings
class InvoiceServiceSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    is_included = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    service = db.relationship('Service')
    
    def __repr__(self):
        return f'<InvoiceServiceSetting {self.service.name} - {self.is_included}>'

# Other Order Types
class OtherOrderType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    validity = db.Column(db.String(50))
    description = db.Column(db.Text)
    required_fields = db.Column(db.Text)  # JSON string of required fields
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<OtherOrderType {self.name}>'

# Other Orders
class OtherOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_type_id = db.Column(db.Integer, db.ForeignKey('other_order_type.id'), nullable=False)
    description = db.Column(db.Text)
    field_data = db.Column(db.Text)  # JSON string of field values
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User')
    order_type = db.relationship('OtherOrderType')
    
    def __repr__(self):
        return f'<OtherOrder {self.id} - {self.order_type.name}>'

# Support Chat
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_admin_message = db.Column(db.Boolean, default=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<ChatMessage {self.id} - User:{self.user_id}>'


class PriceList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PriceList {self.service} ({self.type}): {self.rate}>'
