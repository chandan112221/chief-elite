import json
import os
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import (User, Role, ServiceCategory, Service, StockItem, CheckedItem,
                   FundRequest, FundTransaction, Post, PostComment, PostLike,
                   WebsiteSetting, OtherOrderType, OtherOrder, ChatMessage)
from forms import (LoginForm, RegisterForm, ProfileForm, PasswordChangeForm,
                  FundRequestForm, CommentForm, OtherOrderForm, PostForm)
from utils import is_fund_active, get_website_settings, allowed_to_check

# Home route redirects to login or dashboard
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.is_active:
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Your account has been suspended. Please contact admin.', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form, title='Login')

# Logout route
@app.route('/logout')
@login_required
def logout():
    # Clear any admin session data if it exists
    if 'admin_user_id' in session:
        session.pop('admin_user_id', None)
    logout_user()
    return redirect(url_for('login'))

# Return to admin panel (after logging in as user)
@app.route('/return-to-admin', methods=['POST'])
@login_required
def return_to_admin():
    # Check if there's a stored admin user ID
    admin_id = session.get('admin_user_id')
    if not admin_id:
        flash('No admin session found.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Get the admin user
    admin_user = User.query.get(admin_id)
    if not admin_user or not admin_user.is_admin:
        flash('Invalid admin user.', 'danger')
        session.pop('admin_user_id', None)
        return redirect(url_for('dashboard'))
    
    # Log out as the current user
    logout_user()
    
    # Log back in as the admin
    login_user(admin_user)
    
    # Clear the stored admin ID
    session.pop('admin_user_id', None)
    
    flash('আপনি এখন অ্যাডমিন প্যানেলে ফিরে এসেছেন।', 'success')
    return redirect(url_for('admin_dashboard'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    settings = get_website_settings()
    
    # Get checked items for summary
    checked_items = db.session.query(
        Service.name.label('service_name'),
        Service.id.label('service_id'),
        db.func.count(CheckedItem.id).label('count'),
        db.func.sum(StockItem.rate).label('total'),
        db.func.avg(StockItem.rate).label('rate'),
        db.case((StockItem.is_old == True, 'Old'), else_='New').label('type')
    ).join(StockItem, CheckedItem.stock_item_id == StockItem.id) \
     .join(Service, StockItem.service_id == Service.id) \
     .filter(CheckedItem.user_id == current_user.id) \
     .group_by(Service.id, 'type') \
     .all()
    
    # Fund transactions history
    fund_history = FundTransaction.query.filter_by(user_id=current_user.id).order_by(FundTransaction.created_at.desc()).limit(10).all()
    
    # Fund requests status
    fund_requests = FundRequest.query.filter_by(user_id=current_user.id).order_by(FundRequest.request_date.desc()).limit(5).all()
    
    # Check if user has active funds
    fund_active = is_fund_active(current_user.id)
    
    return render_template('dashboard.html', 
                           title='Dashboard',
                           checked_items=checked_items,
                           fund_history=fund_history,
                           fund_requests=fund_requests,
                           fund_active=fund_active,
                           settings=settings)

# Profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    pwd_form = PasswordChangeForm()
    
    if request.method == 'POST':
        if 'update_profile' in request.form and form.validate_on_submit():
            current_user.full_name = form.full_name.data
            current_user.email = form.email.data
            current_user.phone_number = form.phone_number.data
            current_user.address = form.address.data
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        elif 'change_password' in request.form and pwd_form.validate_on_submit():
            if current_user.check_password(pwd_form.current_password.data):
                current_user.set_password(pwd_form.new_password.data)
                db.session.commit()
                flash('Password changed successfully!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Current password is incorrect!', 'danger')
    
    return render_template('profile.html', 
                          title='My Profile', 
                          form=form, 
                          pwd_form=pwd_form)

# Fund request route
@app.route('/fund/request', methods=['GET', 'POST'])
@login_required
def fund_request():
    settings = get_website_settings()
    form = FundRequestForm()
    
    if form.validate_on_submit():
        new_request = FundRequest(
            user_id=current_user.id,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            transaction_id=form.transaction_id.data
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Fund request submitted successfully! Please wait for admin approval.', 'success')
        return redirect(url_for('dashboard'))
    
    # Get previous fund requests
    previous_requests = FundRequest.query.filter_by(user_id=current_user.id).order_by(FundRequest.request_date.desc()).all()
    
    return render_template('fund_request.html', 
                          title='Request Fund', 
                          form=form, 
                          previous_requests=previous_requests,
                          settings=settings)

# Stock route
@app.route('/stock')
@login_required
def stock():
    settings = get_website_settings()
    
    # Get all services grouped by category
    services_by_category = {}
    all_services = Service.query.all()
    
    for service in all_services:
        category = service.category
        if category.id not in services_by_category:
            services_by_category[category.id] = {
                'category': category,
                'services': []
            }
        services_by_category[category.id]['services'].append(service)
    
    # Get all categories that have services
    categories = [data['category'] for data in services_by_category.values()]
    
    # Set active service category (default to first one)
    active_category = request.args.get('category', None)
    if not active_category and categories:
        active_category = categories[0].name.lower()
    
    # Check if user has active funds to be able to check items
    can_check = is_fund_active(current_user.id) and current_user.balance >= settings.minimum_fund
    
    # Get services for the active category
    active_services = []
    selected_category = None
    
    for category in categories:
        if category.name.lower() == active_category:
            selected_category = category
            break
    
    if selected_category:
        active_services = Service.query.filter_by(category_id=selected_category.id).all()
    
    app.logger.debug(f"Stock page - Active category: {active_category}")
    app.logger.debug(f"Stock page - Available services: {[s.name for s in active_services]}")
    
    return render_template('stock.html', 
                          title='Stock Items', 
                          categories=categories,
                          active_category=active_category,
                          active_services=active_services,
                          can_check=can_check,
                          settings=settings)

# Get stock items by service
@app.route('/stock/<service_name>/<item_type>')
@login_required
def get_stock_items(service_name, item_type):
    app.logger.debug(f"Getting stock items for service: {service_name}, type: {item_type}")
    
    # Skip the rates endpoint - it's handled separately
    if item_type.lower() == 'rates':
        # Just return an empty response for now
        return jsonify({'items': [], 'service': service_name, 'type': item_type, 'count': 0})
    
    # Case insensitive matching for service name
    try:
        service = Service.query.filter(db.func.lower(Service.name) == service_name.lower()).first()
        if not service:
            app.logger.error(f"Service not found: {service_name}")
            return jsonify({
                'error': f"Service '{service_name}' not found", 
                'items': [], 
                'service': service_name,
                'type': item_type,
                'count': 0
            })
        
        app.logger.debug(f"Found service with ID: {service.id}, name: {service.name}")
        
        # Check for role-based restrictions
        if service_name.lower() in ['facebook', 'linkedin'] and current_user.is_mail_user():
            app.logger.debug(f"User is mail_user and cannot access {service_name}")
            return jsonify({'error': 'You do not have permission to view this service'}), 403
        
        if service_name.lower() in ['gmail', 'outlook'] and current_user.is_pass_user():
            app.logger.debug(f"User is pass_user and cannot access {service_name}")
            return jsonify({'error': 'You do not have permission to view this service'}), 403
        
        # Query items based on type (new/old/one time/all)
        if item_type.lower() == 'all':
            # Show all items for this service
            query = StockItem.query.filter_by(service_id=service.id)
            app.logger.debug(f"Query for all items of service: {service.name}")
        elif item_type.lower() == 'one time':
            # For one time, we want non-old items
            query = StockItem.query.filter_by(service_id=service.id, is_old=False)
            app.logger.debug(f"Query for one time (new) items of service: {service.name}")
        else:
            # Filter by old/new status
            is_old = item_type.lower() == 'old'
            query = StockItem.query.filter_by(service_id=service.id, is_old=is_old)
            app.logger.debug(f"Query for {'old' if is_old else 'new'} items of service: {service.name}")
        
        # Get all items from the query
        all_items = query.all()
        app.logger.debug(f"Found {len(all_items)} items matching the criteria")
    except Exception as e:
        app.logger.error(f"Error getting stock items: {str(e)}")
        return jsonify({
            'error': f"Error: {str(e)}", 
            'items': [], 
            'service': service_name,
            'type': item_type,
            'count': 0
        })
    
    # Format items for JSON response
    result = []
    valid_item_index = 1
    
    for item in all_items:
        # Check if item is already checked
        is_checked = db.session.query(CheckedItem).filter_by(stock_item_id=item.id).first() is not None
        
        # Skip items that are already checked
        if is_checked:
            app.logger.debug(f"Skipping item {item.id} because it's already checked")
            continue
        
        item_data = {
            'sl': valid_item_index,
            'id': item.id,
            'name': item.name if service_name.lower() not in ['webmail', 'edu mail'] else None,
            'mail': item.mail,
            'pass': '******',  # Always mask password in listing
            'profile_link': item.profile_link,
            'recovery_mail': item.recovery_mail,
            'two_factor': item.two_factor,
            'rate': float(item.rate) if item.rate is not None else 0.0,  # Ensure rate is a number
            'created_date': item.created_date.strftime('%Y-%m-%d') if item.created_date else None,
            'is_checked': is_checked,
        }
        
        # For webmail/edu mail, show only domain part of email
        if service_name.lower() in ['webmail', 'edu mail'] and item.mail and '@' in item.mail:
            domain = item.mail.split('@')[-1]
            item_data['mail'] = f'***@{domain}'
        
        result.append(item_data)
        valid_item_index += 1
    
    app.logger.debug(f"Returning {len(result)} items after filtering out checked ones")
    return jsonify({
        'items': result, 
        'service': service_name, 
        'type': item_type,
        'count': len(result)
    })

# Check stock item
@app.route('/stock/check/<int:item_id>', methods=['POST'])
@login_required
def check_stock_item(item_id):
    item = StockItem.query.get_or_404(item_id)
    
    # Check if already checked by someone
    existing_check = CheckedItem.query.filter_by(stock_item_id=item_id).first()
    if existing_check:
        return jsonify({'error': 'This item has already been checked'}), 400
    
    # Check if user has sufficient funds
    if current_user.balance < item.rate:
        return jsonify({'error': 'Insufficient funds'}), 400
    
    # Check if user has active funds
    if not is_fund_active(current_user.id):
        return jsonify({'error': 'Your fund request is not active. Please add funds.'}), 400
    
    # Role-based checks
    if not allowed_to_check(current_user, item.service):
        return jsonify({'error': 'You do not have permission to check this item'}), 403
    
    # Create checked item and update user balance
    checked_item = CheckedItem(user_id=current_user.id, stock_item_id=item_id)
    db.session.add(checked_item)
    
    # Deduct funds from user's balance
    current_user.balance -= item.rate
    
    # Record the transaction
    transaction = FundTransaction(
        user_id=current_user.id,
        amount=item.rate,
        transaction_type='deduct',
        description=f'Checked {item.service.name} item'
    )
    db.session.add(transaction)
    
    db.session.commit()
    
    # Return full item details
    item_data = {
        'id': item.id,
        'name': item.name,
        'mail': item.mail,
        'pass': item.password,
        'profile_link': item.profile_link,
        'recovery_mail': item.recovery_mail,
        'two_factor': item.two_factor,
        'rate': item.rate,
        'created_date': item.created_date.isoformat().split('T')[0] if item.created_date else None,
    }
    
    return jsonify({'success': True, 'item': item_data})

# Accounts route (shows checked items)
@app.route('/accounts')
@login_required
def accounts():
    categories = ServiceCategory.query.all()
    
    # Set active service category (default to first one)
    active_category = request.args.get('category', None)
    if not active_category and categories:
        active_category = categories[0].name.lower()
    
    return render_template('accounts.html', 
                          title='My Accounts',
                          categories=categories,
                          active_category=active_category)

# Get checked items by category
@app.route('/accounts/<category_name>')
@login_required
def get_checked_items(category_name):
    # Find category by name
    category = ServiceCategory.query.filter(
        db.func.lower(ServiceCategory.name) == category_name.lower()
    ).first()
    
    if not category:
        return jsonify({'items': [], 'category': category_name})
    
    # Get all services in this category
    services = Service.query.filter_by(category_id=category.id).all()
    
    # Query checked items for this user and all services in the category
    service_ids = [s.id for s in services]
    checked_items = db.session.query(CheckedItem, StockItem, Service).join(
        StockItem, CheckedItem.stock_item_id == StockItem.id
    ).join(
        Service, StockItem.service_id == Service.id
    ).filter(
        CheckedItem.user_id == current_user.id,
        StockItem.service_id.in_(service_ids)
    ).order_by(CheckedItem.checked_at.desc()).all()
    
    # Format items for JSON response
    result = []
    for idx, (checked, item, service) in enumerate(checked_items):
        item_data = {
            'sl': idx + 1,
            'id': item.id,
            'service_name': service.name,
            'name': item.name,
            'mail': item.mail,
            'pass': item.password,
            'profile_link': item.profile_link,
            'recovery_mail': item.recovery_mail,
            'two_factor': item.two_factor,
            'rate': float(item.rate) if item.rate else 0.0,
            'created_date': item.created_date.strftime('%Y-%m-%d') if item.created_date else None,
            'checked_date': checked.checked_at.strftime('%Y-%m-%d') if checked.checked_at else None,
            'is_old': item.is_old
        }
        result.append(item_data)
    
    return jsonify({'items': result, 'category': category_name})

# Other orders route
@app.route('/other-orders', methods=['GET', 'POST'])
@login_required
def other_orders():
    settings = get_website_settings()
    order_types = OtherOrderType.query.filter_by(is_active=True).all()
    form = OtherOrderForm()
    
    # Dynamically populate order type choices
    form.order_type.choices = [(ot.id, f"{ot.name} - {ot.rate} BDT") for ot in order_types]
    
    if form.validate_on_submit():
        selected_type = OtherOrderType.query.get_or_404(form.order_type.data)
        
        # Check if user has sufficient funds
        if current_user.balance < selected_type.rate:
            flash('Insufficient funds to place this order.', 'danger')
            return redirect(url_for('other_orders'))
        
        # Create new order
        new_order = OtherOrder(
            user_id=current_user.id,
            order_type_id=selected_type.id,
            description=form.description.data,
            field_data=json.dumps(form.field_data.data) if form.field_data.data else None
        )
        db.session.add(new_order)
        
        # Deduct funds
        current_user.balance -= selected_type.rate
        
        # Record transaction
        transaction = FundTransaction(
            user_id=current_user.id,
            amount=selected_type.rate,
            transaction_type='deduct',
            description=f'Order for {selected_type.name}'
        )
        db.session.add(transaction)
        
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('other_orders'))
    
    # Get previous orders
    previous_orders = db.session.query(OtherOrder, OtherOrderType).join(
        OtherOrderType, OtherOrder.order_type_id == OtherOrderType.id
    ).filter(
        OtherOrder.user_id == current_user.id
    ).order_by(OtherOrder.created_at.desc()).all()
    
    return render_template('other_orders.html',
                          title='Other Orders',
                          form=form,
                          order_types=order_types,
                          previous_orders=previous_orders,
                          settings=settings)

# Posts route
@app.route('/posts')
@login_required
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    
    return render_template('posts.html', 
                          title='Posts',
                          posts=posts)

# Create post route for regular users
@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    
    if form.validate_on_submit():
        # Create new post
        post = Post(
            admin_id=current_user.id,  # Using admin_id field for the user id
            title=form.title.data,
            content=form.content.data
        )
        
        # Handle photo - either URL or file upload
        if form.photo_file.data:
            # Process uploaded photo file
            photo_file = form.photo_file.data
            photo_filename = secure_filename(photo_file.filename)
            
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join('static', 'uploads', 'posts')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save the file
            photo_path = os.path.join(uploads_dir, photo_filename)
            photo_file.save(photo_path)
            
            # Set the URL to the uploaded file path
            post.photo_url = '/' + photo_path
        elif form.photo_url.data:
            # Use the provided URL
            post.photo_url = form.photo_url.data
        
        # Handle video - either URL or file upload
        if form.video_file.data:
            # Process uploaded video file
            video_file = form.video_file.data
            video_filename = secure_filename(video_file.filename)
            
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join('static', 'uploads', 'posts')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save the file
            video_path = os.path.join(uploads_dir, video_filename)
            video_file.save(video_path)
            
            # Set the URL to the uploaded file path
            post.video_url = '/' + video_path
        elif form.video_url.data:
            # Use the provided URL
            post.video_url = form.video_url.data
        
        db.session.add(post)
        db.session.commit()
        
        flash('Your post has been created successfully!', 'success')
        return redirect(url_for('posts'))
    
    return render_template('create_post.html', 
                          title='Create Post',
                          form=form)

# Post detail route
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    
    # Handle comment submission
    if form.validate_on_submit():
        comment = PostComment(
            post_id=post_id,
            user_id=current_user.id,
            content=form.content.data
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
        return redirect(url_for('post_detail', post_id=post_id))
    
    # Get existing comments
    comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at.desc()).all()
    
    # Check if user has liked the post
    user_like = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    has_liked = user_like is not None
    
    return render_template('post_detail.html',
                          title=post.title,
                          post=post,
                          form=form,
                          comments=comments,
                          has_liked=has_liked)

# Like post route
@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if already liked
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    
    if existing_like:
        # Unlike the post
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'unliked', 'count': len(post.likes) - 1})
    else:
        # Like the post
        like = PostLike(post_id=post_id, user_id=current_user.id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'liked', 'count': len(post.likes) + 1})

# Support chat route
@app.route('/chat')
@login_required
def chat():
    # Get chat history
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at).all()
    
    return render_template('chat.html',
                          title='Support Chat',
                          messages=messages)

# Send chat message
@app.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    content = request.json.get('message')
    
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    message = ChatMessage(
        user_id=current_user.id,
        is_admin_message=False,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'is_admin': message.is_admin_message,
            'timestamp': message.created_at.isoformat().replace('T', ' ').split('.')[0]
        }
    })

# Get new chat messages
@app.route('/chat/messages', methods=['GET'])
@login_required
def get_messages():
    last_id = request.args.get('last_id', 0, type=int)
    
    # Get new messages
    messages = ChatMessage.query.filter(
        ChatMessage.user_id == current_user.id,
        ChatMessage.id > last_id
    ).order_by(ChatMessage.created_at).all()
    
    # Mark admin messages as read
    for message in messages:
        if message.is_admin_message and not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    # Format messages for response
    messages_data = [{
        'id': message.id,
        'content': message.content,
        'is_admin': message.is_admin_message,
        'timestamp': message.created_at.isoformat().replace('T', ' ').split('.')[0]
    } for message in messages]
    
    return jsonify({'messages': messages_data})

# Toggle theme mode
@app.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    theme = request.json.get('theme')
    if current_user.is_authenticated:
        # Could save theme preference in user model if needed
        pass
    
    return jsonify({'success': True, 'theme': theme})
