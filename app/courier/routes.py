from flask import render_template, request, redirect, url_for, session, flash
from app.courier import courier_bp
from app import supabase

# GÜVENLİK KALKANI
@courier_bp.before_request
def require_courier():
    if 'user_id' not in session or session.get('role') != 'courier':
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('auth.login'))

@courier_bp.route('/dashboard')
def dashboard():
    response = supabase.table('deliveries').select(
        'id, status, delivery_date, customers(full_name, address)'
    ).in_('status', ['Hazırlanıyor', 'Dağıtımda']).execute()
    
    return render_template('courier_dashboard.html', deliveries=response.data)

@courier_bp.route('/update_status/<int:delivery_id>', methods=['POST'])
def update_status(delivery_id):
    new_status = request.form.get('status')
    supabase.table('deliveries').update({'status': new_status}).eq('id', delivery_id).execute()
    return redirect(url_for('courier.dashboard'))