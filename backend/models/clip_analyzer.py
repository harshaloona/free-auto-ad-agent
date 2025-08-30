"""
CLIP-based product analysis - COMPLETE VERSION
Save as: backend/models/clip_analyzer.py
"""

import torch
import clip
from PIL import Image
import io
import numpy as np
from typing import Dict, List, Any, Optional

class CLIPAnalyzer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.preprocess = None
        self.model_loaded = False
        
        print(f"🔍 CLIP Analyzer initialized on {self.device}")
    
    def load_model(self):
        """Load CLIP model (lazy loading)"""
        if self.model_loaded:
            return True
            
        try:
            print("📥 Loading CLIP model...")
            self.model, self.preprocess = clip.load("ViT-L/14", device=self.device)
            self.model_loaded = True
            print("✅ CLIP model loaded successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to load CLIP: {e}")
            return False
    
    def analyze_product(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze product image and generate metadata
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with analysis results
        """
        
        if not self.load_model():
            raise Exception("Failed to load CLIP model")
        
        # Load image from bytes
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        # Preprocess for CLIP
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        
        # Analyze product category
        category_analysis = self._analyze_category(image_tensor)
        
        # Analyze visual features
        feature_analysis = self._analyze_features(image_tensor)
        
        # Generate motion recommendations
        motion_style = self._recommend_motion(category_analysis['category'])
        
        # Generate description
        description = self._generate_description(
            category_analysis['category'], 
            feature_analysis
        )
        
        # Generate caption template
        caption_template = self._generate_caption_template(category_analysis['category'])
        
        return {
            'category': category_analysis['category'],
            'category_confidence': category_analysis['confidence'],
            'subcategory': category_analysis.get('subcategory'),
            'features': feature_analysis,
            'motion_style': motion_style,
            'description': description,
            'caption_template': caption_template,
            'color_palette': self._analyze_colors(image),
            'composition': self._analyze_composition(image)
        }
    
    def _analyze_category(self, image_tensor: torch.Tensor) -> Dict[str, Any]:
        """Determine product category"""
        
        # Main categories
        main_categories = [
            "shoes", "sneakers", "boots", "sandals", "heels",
            "clothing", "shirt", "jacket", "dress", "pants", "jeans",
            "electronics", "smartphone", "laptop", "headphones", "tablet",
            "accessories", "watch", "bag", "jewelry", "sunglasses",
            "home decor", "furniture", "lamp", "vase", "pillow",
            "beauty", "makeup", "skincare", "perfume",
            "sports", "fitness equipment", "athletic wear"
        ]
        
        # Generate text queries
        text_queries = [f"a photo of {cat}" for cat in main_categories]
        text_tokens = clip.tokenize(text_queries).to(self.device)
        
        # Get similarities
        with torch.no_grad():
            logits_per_image, _ = self.model(image_tensor, text_tokens)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        
        # Get top matches
        top_indices = np.argsort(probs)[-3:][::-1]  # Top 3
        
        primary_category = main_categories[top_indices[0]]
        confidence = float(probs[top_indices[0]])
        
        # Determine subcategory for specific items
        subcategory = None
        if primary_category in ["shoes", "sneakers", "boots"]:
            subcategory = self._analyze_shoe_type(image_tensor)
        elif primary_category in ["clothing", "shirt", "jacket"]:
            subcategory = self._analyze_clothing_type(image_tensor)
        
        return {
            'category': primary_category,
            'confidence': confidence,
            'subcategory': subcategory,
            'alternatives': [main_categories[i] for i in top_indices[1:3]]
        }
    
    def _analyze_features(self, image_tensor: torch.Tensor) -> Dict[str, float]:
        """Analyze visual features"""
        
        feature_queries = [
            "colorful", "minimalist", "luxury", "modern", "vintage",
            "premium", "elegant", "sporty", "casual", "professional",
            "bright", "dark", "metallic", "matte", "glossy"
        ]
        
        text_tokens = clip.tokenize([f"a {feat} product" for feat in feature_queries]).to(self.device)
        
        with torch.no_grad():
            logits_per_image, _ = self.model(image_tensor, text_tokens)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        
        # Return top features above threshold
        features = {}
        for i, feature in enumerate(feature_queries):
            if probs[i] > 0.1:  # Only include confident features
                features[feature] = float(probs[i])
        
        return dict(sorted(features.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def _analyze_shoe_type(self, image_tensor: torch.Tensor) -> Optional[str]:
        """Specific analysis for shoe products"""
        
        shoe_types = ["running shoes", "dress shoes", "boots", "sandals", "high heels", "sneakers"]
        text_tokens = clip.tokenize([f"a photo of {shoe}" for shoe in shoe_types]).to(self.device)
        
        with torch.no_grad():
            logits_per_image, _ = self.model(image_tensor, text_tokens)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        
        top_idx = np.argmax(probs)
        if probs[top_idx] > 0.3:
            return shoe_types[top_idx]
        return None
    
    def _analyze_clothing_type(self, image_tensor: torch.Tensor) -> Optional[str]:
        """Specific analysis for clothing products"""
        
        clothing_types = ["t-shirt", "dress shirt", "jacket", "hoodie", "dress", "jeans", "formal wear"]
        text_tokens = clip.tokenize([f"a photo of a {cloth}" for cloth in clothing_types]).to(self.device)
        
        with torch.no_grad():
            logits_per_image, _ = self.model(image_tensor, text_tokens)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        
        top_idx = np.argmax(probs)
        if probs[top_idx] > 0.3:
            return clothing_types[top_idx]
        return None
    
    def _recommend_motion(self, category: str) -> str:
        """Recommend best motion type for category"""
        
        motion_map = {
            # Shoes/Footwear - 360° works great
            "shoes": "360_rotation",
            "sneakers": "360_rotation", 
            "boots": "360_rotation",
            
            # Clothing - gentle movement
            "clothing": "gentle_sway",
            "shirt": "gentle_sway",
            "jacket": "gentle_sway",
            "dress": "gentle_sway",
            
            # Electronics - slow orbit to show features
            "electronics": "slow_orbit",
            "smartphone": "slow_orbit",
            "laptop": "slow_orbit",
            "headphones": "360_rotation",
            
            # Accessories - rotation works well
            "accessories": "360_rotation",
            "watch": "360_rotation",
            "jewelry": "360_rotation",
            "bag": "gentle_sway",
            
            # Home decor - zoom focus
            "home decor": "zoom_focus",
            "furniture": "slow_orbit",
            
            # Beauty products - gentle rotation
            "beauty": "gentle_rotation",
            "makeup": "360_rotation"
        }
        
        return motion_map.get(category, "360_rotation")
    
    def _generate_description(self, category: str, features: Dict[str, float]) -> str:
        """Generate product description based on analysis"""
        
        # Base descriptions by category
        base_descriptions = {
            "shoes": "Step up your style game",
            "sneakers": "Performance meets style", 
            "clothing": "Fashion that fits your lifestyle",
            "electronics": "Innovation meets performance",
            "accessories": "The perfect finishing touch",
            "home decor": "Transform your space",
            "beauty": "Elevate your beauty routine",
            "jewelry": "Luxury that speaks to you"
        }
        
        base = base_descriptions.get(category, "Premium quality you can trust")
        
        # Add feature modifiers
        top_feature = max(features.keys(), key=features.get) if features else None
        
        if top_feature:
            if top_feature == "luxury":
                base = f"Luxury {category} that defines elegance"
            elif top_feature == "sporty":
                base = f"Performance-driven {category} for active lifestyles"
            elif top_feature == "minimalist":
                base = f"Clean, modern {category} with timeless appeal"
            elif top_feature == "colorful":
                base = f"Vibrant {category} that makes a statement"
        
        return base
    
    def _generate_caption_template(self, category: str) -> str:
        """Generate social media caption template"""
        
        templates = {
            "shoes": "🔥 Step into comfort. {name} are here for {price}. Tap to shop now. #shoes #style #newdrop",
            "sneakers": "⚡ Fresh kicks alert! {name} for {price}. Get yours before they're gone. #sneakers #fresh #style",
            "clothing": "✨ Style that speaks to you. {name} - {price}. Shop the look. #fashion #style #ootd", 
            "electronics": "⚡ Innovation meets performance. {name} for {price}. Get yours now. #tech #innovation #gadgets",
            "accessories": "💎 The perfect finishing touch. {name} - {price}. Complete your look. #accessories #style #fashion",
            "home decor": "🏠 Transform your space. {name} starting at {price}. Shop now. #homedecor #interiors #lifestyle",
            "jewelry": "✨ Luxury that shines. {name} for {price}. Elevate your style. #jewelry #luxury #style",
            "beauty": "💄 Elevate your routine. {name} for {price}. Glow up starts here. #beauty #skincare #makeup"
        }
        
        return templates.get(category, "🔥 Premium quality. {name} for {price}. Shop now. #quality #premium #shopnow")
    
    def _analyze_colors(self, image: Image.Image) -> List[str]:
        """Extract dominant colors from image"""
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Simple color analysis - get average color from different regions
        h, w = img_array.shape[:2]
        regions = [
            img_array[:h//2, :w//2],  # Top left
            img_array[:h//2, w//2:],  # Top right  
            img_array[h//2:, :w//2],  # Bottom left
            img_array[h//2:, w//2:]   # Bottom right
        ]
        
        color_names = {
            "red": [255, 0, 0],
            "blue": [0, 0, 255], 
            "green": [0, 255, 0],
            "yellow": [255, 255, 0],
            "orange": [255, 165, 0],
            "purple": [128, 0, 128],
            "pink": [255, 192, 203],
            "black": [0, 0, 0],
            "white": [255, 255, 255],
            "gray": [128, 128, 128],
            "brown": [165, 42, 42]
        }
        
        # Find dominant colors
        colors = []
        for region in regions:
            avg_color = np.mean(region.reshape(-1, 3), axis=0)
            
            # Find closest named color
            min_dist = float('inf')
            closest_color = "gray"
            
            for color_name, rgb in color_names.items():
                dist = np.linalg.norm(avg_color - np.array(rgb))
                if dist < min_dist:
                    min_dist = dist
                    closest_color = color_name
            
            if closest_color not in colors and min_dist < 100:
                colors.append(closest_color)
        
        return colors[:3]  # Return top 3 colors
    
    def _analyze_composition(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image composition"""
        
        width, height = image.size
        aspect_ratio = width / height
        
        # Determine orientation
        if aspect_ratio > 1.3:
            orientation = "landscape"
        elif aspect_ratio < 0.8:
            orientation = "portrait"
        else:
            orientation = "square"
        
        return {
            'orientation': orientation,
            'aspect_ratio': round(aspect_ratio, 2),
            'composition': 'centered',
            'recommended_formats': self._get_format_recommendations(orientation)
        }
    
    def _get_format_recommendations(self, orientation: str) -> List[str]:
        """Recommend best ad formats based on image orientation"""
        
        recommendations = {
            "landscape": ["feed", "story"],
            "portrait": ["story", "reels", "feed"],
            "square": ["feed", "story", "reels"]
        }
        
        return recommendations.get(orientation, ["feed", "story", "reels"])
    
    def generate_ad_copy(self, product_name: str, price: str, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate multiple ad copy variations"""
        
        category = analysis.get('category', 'product')
        features = analysis.get('features', {})
        template = analysis.get('caption_template', '')
        
        # Generate variations
        variations = []
        
        # Version 1: Direct from template
        variations.append(template.format(name=product_name, price=price))
        
        # Version 2: Feature-focused
        top_feature = max(features.keys(), key=features.get) if features else 'quality'
        feature_copy = f"🌟 Experience {top_feature} like never before. {product_name} for {price}. Shop now!"
        variations.append(feature_copy)
        
        # Version 3: Urgency-focused  
        urgency_copy = f"⏰ Limited time! {product_name} now {price}. Don't miss out! #limitedtime #shopnow"
        variations.append(urgency_copy)
        
        # Version 4: Benefit-focused
        benefits = {
            "shoes": "comfort and style",
            "clothing": "perfect fit and style", 
            "electronics": "performance and reliability",
            "accessories": "style and functionality"
        }
        benefit = benefits.get(category, "quality and value")
        benefit_copy = f"✨ Discover {benefit}. {product_name} - {price}. Your new favorite! #quality #style"
        variations.append(benefit_copy)
        
        return {
            'primary': variations[0],
            'feature_focused': variations[1], 
            'urgency': variations[2],
            'benefit_focused': variations[3]
        }
    
    def get_hashtag_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate relevant hashtags"""
        
        category = analysis.get('category', '')
        features = list(analysis.get('features', {}).keys())
        
        # Base hashtags by category
        hashtag_map = {
            "shoes": ["#shoes", "#footwear", "#style", "#fashion"],
            "sneakers": ["#sneakers", "#kicks", "#streetwear", "#style"],
            "clothing": ["#fashion", "#style", "#ootd", "#clothing"],
            "electronics": ["#tech", "#gadgets", "#innovation", "#electronics"],
            "accessories": ["#accessories", "#fashion", "#style", "#luxury"],
            "beauty": ["#beauty", "#makeup", "#skincare", "#selfcare"]
        }
        
        base_tags = hashtag_map.get(category, ["#product", "#quality", "#style"])
        
        # Add feature-based hashtags
        feature_tags = []
        for feature in features[:2]:  # Top 2 features
            feature_tags.append(f"#{feature}")
        
        # Combine and deduplicate
        all_tags = base_tags + feature_tags + ["#shopnow", "#newcollection"]
        
        return list(dict.fromkeys(all_tags))[:8]  # Remove duplicates, max 8 tags