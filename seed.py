import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# .env dosyasındaki bilgileri yükle
load_dotenv()

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def seed_data():
    print("Test verileri Supabase'e ekleniyor, lütfen bekleyin...")
    
    try:
        # 1. Örnek Müşteriler Ekle
        customer_data = [
            {"full_name": "Ahmet Yılmaz", "email": "ahmet.y@example.com", "phone": "05551112233", "address": "Kadıköy, İstanbul"},
            {"full_name": "Ayşe Demir", "email": "ayse.d@example.com", "phone": "05324445566", "address": "Beşiktaş, İstanbul"}
        ]
        customers = supabase.table("customers").insert(customer_data).execute()
        
        # 2. Örnek Stok/Envanter Ekle
        inventory_data = [
            {"product_name": "Yetişkin Köpek Maması 15kg", "stock_count": 50, "price": 1200.00},
            {"product_name": "Yavru Kedi Maması 5kg", "stock_count": 100, "price": 450.00}
        ]
        inventory = supabase.table("inventory").insert(inventory_data).execute()
        
        # 3. Örnek Kurye Ekle
        courier_data = [
            {"full_name": "Hasan Hızlı", "phone": "05449998877", "vehicle_plate": "34 ABC 123"}
        ]
        couriers = supabase.table("couriers").insert(courier_data).execute()
        
        # Veriler başarıyla eklendiyse ID'lerini alıp teslimat ve oturum bilgilerini oluşturalım
        if customers.data and couriers.data and inventory.data:
            c1_id = customers.data[0]['id']
            c2_id = customers.data[1]['id']
            cour_id = couriers.data[0]['id']
            prod1_id = inventory.data[0]['id']
            prod2_id = inventory.data[1]['id']
            
            today = datetime.now().date().isoformat()
            tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            
            # 4. Örnek Paketler/Teslimatlar Ekle
            delivery_data = [
                {
                    "customer_id": c1_id,
                    "courier_id": cour_id,
                    "status": "Hazırlanıyor",
                    "delivery_date": today,
                    "items": [{"product_id": prod1_id, "quantity": 1}]
                },
                {
                    "customer_id": c2_id,
                    "courier_id": cour_id,
                    "status": "Dağıtımda",
                    "delivery_date": tomorrow,
                    "items": [{"product_id": prod2_id, "quantity": 2}]
                },
                {
                    "customer_id": c1_id,
                    "courier_id": cour_id,
                    "status": "Hazırlanıyor",
                    "delivery_date": yesterday,
                    "items": [{"product_id": prod1_id, "quantity": 1}]
                }
            ]
            supabase.table("deliveries").insert(delivery_data).execute()

            # 5. Sisteme Giriş Yapacak Kullanıcıları Ekle (Auth)
            users_data = [
                {"username": "yonetici", "password_hash": generate_password_hash("admin123"), "role": "admin", "reference_id": None},
                {"username": "musteri_ahmet", "password_hash": generate_password_hash("musteri123"), "role": "customer", "reference_id": c1_id},
                {"username": "kurye_hasan", "password_hash": generate_password_hash("kurye123"), "role": "courier", "reference_id": cour_id}
            ]
            supabase.table("users").insert(users_data).execute()

            print("Tebrikler! Test verileri ve giriş kullanıcıları başarıyla oluşturuldu.")
            
    except Exception as e:
        print(f"Veri eklenirken bir hata oluştu: {e}")

if __name__ == "__main__":
    seed_data()