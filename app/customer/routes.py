from flask import render_template, session, redirect, url_for, flash
from app.customer import customer_bp
from app import supabase

# GÜVENLİK KALKANI
@customer_bp.before_request
def require_customer():
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('auth.login'))

@customer_bp.route('/dashboard')
def dashboard():
    # Artık sabit "1" yerine, giriş yapan müşterinin gerçek ID'sini session'dan alıyoruz
    customer_id = session.get('reference_id') 
    
    response = supabase.table('deliveries').select('*').eq('customer_id', customer_id).execute()
    my_deliveries = response.data
    
    return render_template('customer_dashboard.html', deliveries=my_deliveries)