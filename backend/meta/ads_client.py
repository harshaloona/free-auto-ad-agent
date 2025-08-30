        # Generate mock IDs
        creative_id = f"sandbox_creative_{hash(product_info['name']) % 100000}"
        
        mock_videos = []
        for video in videos:
            mock_videos.append({
                'format': video['format'],
                'media_id': f"mock_media_{hash(video['format']) % 10000}",
                'status': 'uploaded'
            })
        
        return {
            'creative_id': creative_id,
            'uploaded_videos': mock_videos,
            'preview_urls': {
                'feed': f"https://facebook.com/ads/preview/{creative_id}/feed",
                'story': f"https://facebook.com/ads/preview/{creative_id}/story"
            },
            'status': 'sandbox_created',
            'message': 'Sandbox mode - no real ads created'
        }
    
    def _upload_video(self, video_path: str, format_name: str) -> str:
        """Upload video to Meta Media Library"""
        
        url = f"{self.base_url}/{self.ad_account_id}/advideos"
        
        with open(video_path, 'rb') as video_file:
            files = {'file': video_file}
            data = {
                'access_token': self.access_token,
                'name': f"AI Generated Video - {format_name}",
                'file_url': ''  # Using direct upload
            }
            
            response = requests.post(url, files=files, data=data)
            
        if response.status_code != 200:
            raise Exception(f"Video upload failed: {response.text}")
        
        result = response.json()
        return result['id']
    
    def _prepare_creative_data(self, uploaded_videos: List[Dict], product_info: Dict[str, Any]) -> Dict:
        """Prepare ad creative data structure"""
        
        # Use the first video as primary (usually feed format)
        primary_video = uploaded_videos[0]
        
        creative_data = {
            'name': f"AI Video Ad - {product_info['name']}",
            'object_story_spec': {
                'page_id': self.page_id,
                'video_data': {
                    'video_id': primary_video['media_id'],
                    'title': product_info['name'],
                    'message': product_info['description'],
                    'call_to_action': {
                        'type': 'SHOP_NOW',
                        'value': {
                            'link': product_info['url'],
                            'link_title': 'Shop Now'
                        }
                    }
                }
            },
            'degrees_of_freedom_spec': {
                'creative_features_spec': {
                    'standard_enhancements': {
                        'enroll_status': 'OPT_IN'
                    }
                }
            }
        }
        
        # Add Instagram placement if actor ID provided
        if self.instagram_actor_id:
            creative_data['instagram_actor_id'] = self.instagram_actor_id
        
        return creative_data
    
    def _create_creative(self, creative_data: Dict) -> str:
        """Create ad creative via Meta API"""
        
        url = f"{self.base_url}/{self.ad_account_id}/adcreatives"
        
        data = creative_data.copy()
        data['access_token'] = self.access_token
        
        response = requests.post(url, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Creative creation failed: {response.text}")
        
        result = response.json()
        return result['id']
    
    def _get_preview_urls(self, creative_id: str) -> Dict[str, str]:
        """Get preview URLs for the created ad creative"""
        
        url = f"{self.base_url}/{creative_id}/previews"
        
        params = {
            'access_token': self.access_token,
            'ad_format': 'DESKTOP_FEED_STANDARD'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('data'):
                return {
                    'feed': result['data'][0].get('body', ''),
                    'mobile': result['data'][0].get('body', '')  # Same for now
                }
        
        return {
            'feed': f"https://facebook.com/ads/preview/{creative_id}",
            'mobile': f"https://facebook.com/ads/preview/{creative_id}"
        }
    
    def create_ad_set(self, creative_id: str, daily_budget: int = 1000) -> str:
        """Create ad set for the creative"""
        
        if self.sandbox_mode:
            return f"sandbox_adset_{hash(creative_id) % 10000}"
        
        url = f"{self.base_url}/{self.ad_account_id}/adsets"
        
        data = {
            'access_token': self.access_token,
            'name': f"AI Generated Ad Set - {creative_id[:8]}",
            'campaign_id': self._get_or_create_campaign(),
            'daily_budget': daily_budget,  # Budget in cents
            'billing_event': 'IMPRESSIONS',
            'optimization_goal': 'REACH',
            'bid_amount': 100,  # Bid in cents
            'targeting': {
                'geo_locations': {'countries': ['US']},
                'age_min': 18,
                'age_max': 65
            },
            'status': 'PAUSED'  # Create paused for review
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Ad set creation failed: {response.text}")
        
        result = response.json()
        return result['id']
    
    def create_ad(self, creative_id: str, ad_set_id: str) -> str:
        """Create final ad"""
        
        if self.sandbox_mode:
            return f"sandbox_ad_{hash(creative_id + ad_set_id) % 10000}"
        
        url = f"{self.base_url}/{self.ad_account_id}/ads"
        
        data = {
            'access_token': self.access_token,
            'name': f"AI Video Ad - {creative_id[:8]}",
            'adset_id': ad_set_id,
            'creative': {'creative_id': creative_id},
            'status': 'PAUSED'  # Create paused for review
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Ad creation failed: {response.text}")
        
        result = response.json()
        return result['id']
    
    def _get_or_create_campaign(self) -> str:
        """Get existing campaign or create new one"""
        
        # Try to find existing AI campaign
        url = f"{self.base_url}/{self.ad_account_id}/campaigns"
        params = {
            'access_token': self.access_token,
            'fields': 'id,name',
            'limit': 25
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            campaigns = response.json().get('data', [])
            
            # Look for existing AI campaign
            for campaign in campaigns:
                if 'AI Generated' in campaign.get('name', ''):
                    return campaign['id']
        
        # Create new campaign
        return self._create_campaign()
    
    def _create_campaign(self) -> str:
        """Create new campaign for AI-generated ads"""
        
        url = f"{self.base_url}/{self.ad_account_id}/campaigns"
        
        data = {
            'access_token': self.access_token,
            'name': 'AI Generated Video Ads',
            'objective': 'OUTCOME_TRAFFIC',
            'status': 'ACTIVE',
            'special_ad_categories': []
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code != 200:
            raise Exception(f"Campaign creation failed: {response.text}")
        
        result = response.json()
        return result['id']
    
    def get_ad_performance(self, ad_id: str) -> Dict[str, Any]:
        """Get performance metrics for an ad"""
        
        if self.sandbox_mode:
            return {
                'impressions': 1250,
                'clicks': 45,
                'ctr': 3.6,
                'cpc': 0.75,
                'spend': 33.75,
                'status': 'sandbox_data'
            }
        
        url = f"{self.base_url}/{ad_id}/insights"
        
        params = {
            'access_token': self.access_token,
            'fields': 'impressions,clicks,ctr,cpc,spend',
            'date_preset': 'last_7d'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                return data[0]
        
        return {}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Meta API connection"""
        
        if self.sandbox_mode:
            return {
                'status': 'sandbox_mode',
                'message': 'Sandbox mode - no real API calls made',
                'ad_account_access': True,
                'page_access': True
            }
        
        if not self.access_token:
            return {
                'status': 'error',
                'message': 'META_ACCESS_TOKEN not provided',
                'ad_account_access': False,
                'page_access': False
            }
        
        # Test ad account access
        try:
            url = f"{self.base_url}/{self.ad_account_id}"
            params = {'access_token': self.access_token, 'fields': 'name,id'}
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                account_info = response.json()
                return {
                    'status': 'connected',
                    'ad_account_name': account_info.get('name'),
                    'ad_account_id': account_info.get('id'),
                    'ad_account_access': True,
                    'page_access': bool(self.page_id)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'API Error: {response.text}',
                    'ad_account_access': False,
                    'page_access': False
                }
                
        except Exception as e:
            return {
                'status': 'error', 
                'message': str(e),
                'ad_account_access': False,
                'page_access': False
            }"""
Meta (Facebook/Instagram) Ads integration
Save as: backend/meta/ads_client.py
"""

import os
import requests
from typing import Dict, List, Any, Optional
import json

class MetaAdsClient:
    def __init__(self):
        self.access_token = os.getenv('META_ACCESS_TOKEN')
        self.ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
        self.page_id = os.getenv('META_PAGE_ID')
        self.instagram_actor_id = os.getenv('META_INSTAGRAM_ACTOR_ID')
        self.sandbox_mode = os.getenv('META_SANDBOX_MODE', 'true').lower() == 'true'
        
        self.base_url = "https://graph.facebook.com/v18.0"
        
        print(f"📘 Meta Ads client initialized (sandbox: {self.sandbox_mode})")
    
    def create_ad_creative(self, videos: List[Dict], product_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create ad creative with generated videos
        
        Args:
            videos: List of video dictionaries with paths and formats
            product_info: Product information (name, price, url, description)
            
        Returns:
            Dict with creative_id and preview URLs
        """
        
        if self.sandbox_mode:
            return self._create_sandbox_creative(videos, product_info)
        
        if not self.access_token:
            raise Exception("META_ACCESS_TOKEN required for real ad creation")
        
        try:
            # Upload videos to Meta Media Library
            uploaded_videos = []
            for video in videos:
                media_id = self._upload_video(video['video_path'], video['format'])
                uploaded_videos.append({
                    'format': video['format'],
                    'media_id': media_id
                })
            
            # Create ad creative
            creative_data = self._prepare_creative_data(uploaded_videos, product_info)
            creative_id = self._create_creative(creative_data)
            
            # Generate preview URLs
            preview_urls = self._get_preview_urls(creative_id)
            
            return {
                'creative_id': creative_id,
                'uploaded_videos': uploaded_videos,
                'preview_urls': preview_urls,
                'status': 'created'
            }
            
        except Exception as e:
            print(f"❌ Meta API error: {e}")
            raise Exception(f"Failed to create Meta ad creative: {e}")
    
    def _create_sandbox_creative(self, videos: List[Dict], product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock creative for testing"""
        
        print("🧪 Creating sandbox ad creative (no real API calls)")
        
        # Generate mock IDs
        creative_id = f"sandbox_creative_{hash(product_info['name']) % 100000}"
        