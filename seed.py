from app.db.database import SessionLocal, engine, Base
from app.core.security import hash_password
import app.models 

from app.models.user import User
from app.models.campaign import Campaign, CampaignMember
from app.models.campaign_task import CampaignTask

def seed_data():

    print("Đang làm sạch CSDL...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = User(email="admin@marketing.com", password_hash=hash_password("admin123"), full_name="System Admin", role="ADMIN")
        user1 = User(email="owner@marketing.com", password_hash=hash_password("user123"), full_name="Campaign Lead", role="USER")
        user2 = User(email="designer@marketing.com", password_hash=hash_password("user123"), full_name="Creative Designer", role="USER")
        
        db.add_all([admin, user1, user2])
        db.commit()

        campaign1 = Campaign(name="Chiến dịch Tết 2026", description="Quảng bá sản phẩm mùa Tết", owner_id=user1.id)
        db.add(campaign1)
        db.commit()

        m1 = CampaignMember(campaign_id=campaign1.id, user_id=user1.id, role="OWNER")
        m2 = CampaignMember(campaign_id=campaign1.id, user_id=user2.id, role="MEMBER")
        db.add_all([m1, m2])
        db.commit()

        task1 = CampaignTask(
            campaign_id=campaign1.id,
            title="Thiết kế Banner Facebook",
            description="Banner tỉ lệ 16:9 chủ đề Tết",
            priority="HIGH",
            status="IN_PROGRESS",
            assignee_id=user2.id
        )
        db.add(task1)

        campaign2 = Campaign(name="Chiến dịch Ra Mắt Sản Phẩm Mới", description="Quảng bá dòng sản phẩm Q3/2026", owner_id=user1.id)
        db.add(campaign2)
        db.commit()

        m3 = CampaignMember(campaign_id=campaign2.id, user_id=user1.id, role="OWNER")
        m4 = CampaignMember(campaign_id=campaign2.id, user_id=user2.id, role="MEMBER")
        db.add_all([m3, m4])
        db.commit()

        task2 = CampaignTask(
            campaign_id=campaign2.id,
            title="Viết bài PR báo chí",
            description="Soạn thảo nội dung bài viết ra mắt sản phẩm",
            priority="MEDIUM",
            status="TODO",
            assignee_id=user1.id
        )
        task3 = CampaignTask(
            campaign_id=campaign2.id,
            title="Lên kịch bản Video Landing Page",
            description="Kịch bản video giới thiệu tính năng nổi bật",
            priority="HIGH",
            status="DONE",
            assignee_id=user2.id
        )
        db.add_all([task2, task3])
        
        db.commit()
        print("Seed dữ liệu mẫu (2 chiến dịch & 3 tasks) thành công!")
    except Exception as e:
        db.rollback()
        print("Lỗi seed dữ liệu:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()