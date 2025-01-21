from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db, app
from werkzeug.security import generate_password_hash




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(32), unique=False, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(50),nullable=False)
    role = db.Column(db.String(50),nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    is_flag = db.Column(db.Boolean, default=False, nullable=False)
    # @property
    # def passwords(self):


class Infl_platform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youtube = db.Column(db.Boolean, nullable=False)
    twitter = db.Column(db.Boolean, nullable=False)
    instagram = db.Column(db.Boolean, nullable=False)

class Spon_industry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    industry= db.Column(db.String(50),nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_name = db.Column(db.String(50),nullable=False)
    campaign_name = db.Column(db.String(50),nullable=False)
    niche = db.Column(db.String(50),nullable=False)
    description = db.Column(db.String(250),nullable=True)
    start_date = db.Column(db.Date,nullable=False)
    end_date = db.Column(db.Date,nullable=False)
    status = db.Column(db.String(50),default="active",nullable=False)
    budget = db.Column(db.Integer,nullable=False)
    category = db.Column(db.String(50),nullable=True)    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    private = db.Column(db.Boolean, default=False)
    industry_name = db.Column(db.Integer,db.ForeignKey('spon_industry.id'), nullable=False)
    ads = db.relationship('Ads', backref='campaign' , lazy=True, cascade='all, delete-orphan')
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)
    

class Ads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100),nullable=False)
    category = db.Column(db.String(50),nullable=True) 
    description = db.Column(db.String(250),nullable=True)
    payment = db.Column(db.Integer,nullable=False)
    # num_videos = db.Column(db.Integer,nullable=True)
    terms = db.Column(db.String(250),nullable=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey("influencer.id"))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)
    evidence_url = db.Column(db.String(250),nullable=True)
    

class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    niche = db.Column(db.String(50),nullable=True)
    platform = db.Column(db.Integer,db.ForeignKey('infl_platform.id'),nullable=False)
    earnings = db.Column(db.Integer,default=0,nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    image_path = db.Column(db.String(100),default="default.jpg",nullable=True)
    
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ads_id = db.Column(db.Integer,db.ForeignKey('ads.id'),nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # requester_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50),nullable=False)
    date = db.Column(db.DateTime, nullable=False)

class Negotiate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requested_by = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    status = db.Column(db.String(50),nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    modified_by = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    request_id = db.Column(db.Integer,db.ForeignKey('request.id'),nullable=False)
    old_amount = db.Column(db.Integer, default=0,nullable=False)
    new_amount = db.Column(db.Integer, default=0,nullable=False)

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    image_path = db.Column(db.String(100),default="default.jpg",nullable=True)
    industry = db.Column(db.Integer,db.ForeignKey('spon_industry.id'),nullable=False)
    
class Ratings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    rating = db.Column(db.Integer,nullable=False)
    count = db.Column(db.Integer,default=0,nullable=False)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating_id = db.Column(db.Integer, db.ForeignKey('ratings.id'),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    description = db.Column(db.String(250),nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    rating = db.Column(db.Integer,nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)



    





    
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(username="admin", password=generate_password_hash("admin"),name='Admin',email='admin@gmail.com',role='admin',gender='female')
        db.session.add(admin)
        db.session.commit()
