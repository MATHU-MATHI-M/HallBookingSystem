from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_
from datetime import datetime, timedelta

from app import app, db
from models import User, Hall, Booking
from forms import LoginForm, RegistrationForm, BookingForm, HallForm, BookingAdminForm
import logging

# Add current date to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    # Get a few upcoming approved events for the homepage
    upcoming_events = Booking.query.filter(
        Booking.status == 'approved',
        Booking.start_time > datetime.now()
    ).order_by(Booking.start_time).limit(5).all()
    
    # Get hall statistics
    seminar_halls = Hall.query.filter_by(hall_type='seminar', is_active=True).count()
    computer_centers = Hall.query.filter_by(hall_type='computer', is_active=True).count()
    active_bookings = Booking.query.filter_by(status='approved').filter(Booking.end_time > datetime.now()).count()
    
    return render_template('index.html', 
                           upcoming_events=upcoming_events,
                           seminar_halls=seminar_halls,
                           computer_centers=computer_centers,
                           active_bookings=active_bookings)


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.is_admin:
                login_user(user, remember=form.remember_me.data)
                flash('Welcome Admin!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('This account does not have admin privileges', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    return render_template('admin_login.html', form=form)

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_admin:
                login_user(user, remember=form.remember_me.data)
                flash('Successfully logged in!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Please use admin login for admin accounts', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    return render_template('user_login.html', form=form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            if user.is_admin:
                next_page = url_for('admin_dashboard')
            else:
                next_page = url_for('index')
        
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('login.html', title='Choose Registration Type')

@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('user_login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            print(f"Registration error: {str(e)}")
    
    return render_template('register.html', title='User Register', form=form)

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        admin = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        flash('Admin registration successful! You can now log in.', 'success')
        return redirect(url_for('admin_login'))
    
    return render_template('admin/register.html', title='Admin Register', form=form)


@app.route('/halls')
def halls():
    hall_type = request.args.get('type', 'all')
    
    # Add static hall images
    hall_images = {
        'seminar': '/static/images/seminar-hall.jpg',
        'computer': '/static/images/computer-lab.jpg'
    }
    
    if hall_type == 'seminar':
        halls = Hall.query.filter_by(hall_type='seminar', is_active=True).all()
    elif hall_type == 'computer':
        halls = Hall.query.filter_by(hall_type='computer', is_active=True).all()
    else:
        halls = Hall.query.filter_by(is_active=True).all()
    
    return render_template('halls.html', title='Halls', halls=halls, hall_type=hall_type)


@app.route('/hall/<int:hall_id>')
def hall_detail(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    
    # Get upcoming bookings for this hall
    upcoming_bookings = Booking.query.filter(
        Booking.hall_id == hall_id,
        Booking.status == 'approved',
        Booking.end_time >= datetime.now()
    ).order_by(Booking.start_time).all()
    
    return render_template('hall_detail.html', hall=hall, upcoming_bookings=upcoming_bookings)


@app.route('/booking/new', methods=['GET', 'POST'])
@login_required
def create_booking():
    form = BookingForm()
    
    # Populate hall choices dynamically
    active_halls = Hall.query.filter_by(is_active=True).all()
    form.hall_id.choices = [(h.id, f"{h.name} ({h.hall_type.capitalize()})") for h in active_halls]
    
    if form.validate_on_submit():
        # Check if the hall is available for the requested time
        hall = Hall.query.get(form.hall_id.data)
        if not hall:
            flash('Selected hall does not exist', 'danger')
            return redirect(url_for('create_booking'))
        
        # Check for booking conflicts
        conflicting_bookings = Booking.query.filter(
            Booking.hall_id == form.hall_id.data,
            Booking.status == 'approved',
            or_(
                and_(Booking.start_time <= form.start_time.data, Booking.end_time > form.start_time.data),
                and_(Booking.start_time < form.end_time.data, Booking.end_time >= form.end_time.data),
                and_(Booking.start_time >= form.start_time.data, Booking.end_time <= form.end_time.data)
            )
        ).first()
        
        if conflicting_bookings:
            flash('This hall is already booked for the selected time period.', 'danger')
            return render_template('booking.html', form=form, title="New Booking")
        
        booking = Booking(
            user_id=current_user.id,
            hall_id=form.hall_id.data,
            event_name=form.event_name.data,
            event_description=form.event_description.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            attendees=form.attendees.data,
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        flash('Your booking request has been submitted and is pending approval.', 'success')
        return redirect(url_for('my_bookings'))
    
    return render_template('booking.html', form=form, title="New Booking")


@app.route('/bookings')
@login_required
def my_bookings():
    # Get all bookings for the current user
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.start_time.desc()).all()
    return render_template('bookings.html', bookings=bookings, title="My Bookings")


@app.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user or user is admin
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to cancel this booking.', 'danger')
        return redirect(url_for('my_bookings'))
    
    # Can only cancel pending or approved bookings
    if booking.status not in ['pending', 'approved']:
        flash('This booking cannot be canceled.', 'danger')
        return redirect(url_for('my_bookings'))
    
    booking.status = 'cancelled'
    db.session.commit()
    flash('Booking has been cancelled successfully.', 'success')
    
    if current_user.is_admin:
        return redirect(url_for('admin_manage_bookings'))
    else:
        return redirect(url_for('my_bookings'))


@app.route('/api/availability')
def check_availability():
    hall_id = request.args.get('hall_id', type=int)
    date = request.args.get('date')
    
    if not hall_id or not date:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        start_of_day = datetime.combine(date_obj, datetime.min.time())
        end_of_day = datetime.combine(date_obj, datetime.max.time())
        
        # Get all approved bookings for the specified hall and date
        bookings = Booking.query.filter(
            Booking.hall_id == hall_id,
            Booking.status == 'approved',
            Booking.start_time <= end_of_day,
            Booking.end_time >= start_of_day
        ).all()
        
        booking_data = []
        for booking in bookings:
            booking_data.append({
                'id': booking.id,
                'event_name': booking.event_name,
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M')
            })
        
        return jsonify({'bookings': booking_data})
    
    except Exception as e:
        logging.error(f"Error in check_availability: {str(e)}")
        return jsonify({'error': 'An error occurred while checking availability'}), 500


# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Statistics for dashboard
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    approved_bookings = Booking.query.filter_by(status='approved').count()
    total_halls = Hall.query.count()
    total_users = User.query.count()
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    # Upcoming events
    upcoming_events = Booking.query.filter(
        Booking.status == 'approved',
        Booking.start_time > datetime.now()
    ).order_by(Booking.start_time).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           total_bookings=total_bookings,
                           pending_bookings=pending_bookings,
                           approved_bookings=approved_bookings,
                           total_halls=total_halls,
                           total_users=total_users,
                           recent_bookings=recent_bookings,
                           upcoming_events=upcoming_events)


@app.route('/admin/bookings')
@login_required
def admin_manage_bookings():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    status_filter = request.args.get('status', 'all')
    
    if status_filter != 'all':
        bookings = Booking.query.filter_by(status=status_filter).order_by(Booking.created_at.desc()).all()
    else:
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    
    return render_template('admin/manage_bookings.html', bookings=bookings, current_filter=status_filter)


@app.route('/admin/booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def admin_booking_detail(booking_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    form = BookingAdminForm(obj=booking)
    
    if form.validate_on_submit():
        old_status = booking.status
        booking.status = form.status.data
        
        # If status changed to approved or rejected, set the admin who made the decision
        if old_status == 'pending' and booking.status in ['approved', 'rejected']:
            booking.approved_by = current_user.id
        
        db.session.commit()
        
        flash(f'Booking status updated to {booking.status.capitalize()}.', 'success')
        return redirect(url_for('admin_manage_bookings'))
    
    return render_template('admin/booking_detail.html', booking=booking, form=form)


@app.route('/admin/halls')
@login_required
def admin_manage_halls():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    halls = Hall.query.all()
    return render_template('admin/manage_halls.html', halls=halls)


@app.route('/admin/hall/new', methods=['GET', 'POST'])
@login_required
def admin_create_hall():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    form = HallForm()
    
    if form.validate_on_submit():
        hall = Hall(
            name=form.name.data,
            hall_type=form.hall_type.data,
            capacity=form.capacity.data,
            description=form.description.data,
            features=form.features.data,
            image_url=form.image_url.data,
            is_active=form.is_active.data
        )
        
        db.session.add(hall)
        db.session.commit()
        
        flash('New hall created successfully.', 'success')
        return redirect(url_for('admin_manage_halls'))
    
    return render_template('admin/hall_form.html', form=form, title="Create New Hall")


@app.route('/admin/hall/<int:hall_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_hall(hall_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    hall = Hall.query.get_or_404(hall_id)
    form = HallForm(obj=hall)
    
    if form.validate_on_submit():
        hall.name = form.name.data
        hall.hall_type = form.hall_type.data
        hall.capacity = form.capacity.data
        hall.description = form.description.data
        hall.features = form.features.data
        hall.image_url = form.image_url.data
        hall.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('Hall updated successfully.', 'success')
        return redirect(url_for('admin_manage_halls'))
    
    return render_template('admin/hall_form.html', form=form, hall=hall, title="Edit Hall")


@app.route('/admin/users')
@login_required
def admin_manage_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)


@app.route('/admin/user/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
def admin_toggle_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin rights from oneself
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'danger')
        return redirect(url_for('admin_manage_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    action = "granted" if user.is_admin else "revoked"
    flash(f'Admin privileges {action} for {user.username}.', 'success')
    return redirect(url_for('admin_manage_users'))


# API routes for calendar
@app.route('/api/events')
def get_events():
    start = request.args.get('start')
    end = request.args.get('end')
    hall_id = request.args.get('hall_id', type=int)
    
    if not start or not end:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        query = Booking.query.filter(
            Booking.status == 'approved',
            Booking.start_time <= end_date,
            Booking.end_time >= start_date
        )
        
        if hall_id:
            query = query.filter(Booking.hall_id == hall_id)
        
        bookings = query.all()
        
        events = []
        for booking in bookings:
            hall = Hall.query.get(booking.hall_id)
            events.append({
                'id': booking.id,
                'title': booking.event_name,
                'start': booking.start_time.isoformat(),
                'end': booking.end_time.isoformat(),
                'extendedProps': {
                    'hall': hall.name,
                    'description': booking.event_description,
                    'status': booking.status
                },
                'backgroundColor': '#007bff' if hall.hall_type == 'seminar' else '#28a745'
            })
        
        return jsonify(events)
    
    except Exception as e:
        logging.error(f"Error in get_events: {str(e)}")
        return jsonify({'error': 'An error occurred while fetching events'}), 500


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.route('/admin/hall/<int:hall_id>/delete', methods=['POST'])
@login_required
def admin_delete_hall(hall_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    hall = Hall.query.get_or_404(hall_id)
    if hall.bookings.filter_by(status='approved').first():
        flash('Cannot delete hall with approved bookings.', 'danger')
        return redirect(url_for('admin_manage_halls'))
    
    db.session.delete(hall)
    db.session.commit()
    flash('Hall deleted successfully.', 'success')
    return redirect(url_for('admin_manage_halls'))
@app.route('/incharge/login', methods=['GET', 'POST'])
def incharge_login():
    if current_user.is_authenticated:
        if current_user.is_hall_incharge:
            return redirect(url_for('incharge_dashboard'))
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('incharge_login'))
        
        if not user.is_hall_incharge:
            flash('Access denied. Hall incharge privileges required.', 'danger')
            return redirect(url_for('incharge_login'))
        
        login_user(user, remember=form.remember_me.data)
        flash('You have been logged in successfully!', 'success')
        return redirect(url_for('incharge_dashboard'))
    
    return render_template('incharge/login.html', title='Hall Incharge Login', form=form)

@app.route('/incharge/dashboard')
@login_required
def incharge_dashboard():
    if not current_user.is_hall_incharge:
        flash('Access denied. Hall incharge privileges required.', 'danger')
        return redirect(url_for('index'))
    
    pending_bookings = Booking.query.join(Hall).filter(
        Hall.incharge_id == current_user.id,
        Booking.status == 'pending'
    ).all()
    
    return render_template('incharge/dashboard.html', 
                         pending_bookings=pending_bookings,
                         title='Hall Incharge Dashboard')

@app.route('/incharge/booking/<int:booking_id>/approve', methods=['POST'])
@login_required
def approve_booking(booking_id):
    if not current_user.is_hall_incharge:
        flash('Access denied. Hall incharge privileges required.', 'danger')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    if booking.hall.incharge_id != current_user.id:
        flash('Access denied. You can only manage your assigned halls.', 'danger')
        return redirect(url_for('incharge_dashboard'))
    
    booking.status = 'approved'
    booking.approved_by = current_user.id
    db.session.commit()
    
    flash('Booking has been approved successfully.', 'success')
    return redirect(url_for('incharge_dashboard'))
@app.route('/admin/booking/<int:booking_id>/update-status', methods=['POST'])
@login_required
def admin_update_booking_status(booking_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'approved', 'rejected']:
        booking.status = new_status
        db.session.commit()
        flash(f'Booking status updated to {new_status}.', 'success')
    
    return redirect(url_for('admin_manage_bookings'))
