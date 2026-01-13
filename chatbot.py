"""
Product Information Chatbot System
AI-powered chatbot for answering product and service inquiries
Supports both Arabic and English languages with role-based access control
"""

import json
import os
import sys
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from pathlib import Path
from openai import OpenAI

class UserRole(Enum):
    """User roles with different permission levels"""
    CUSTOMER = "customer"
    STAFF = "staff"


class ProductChatbot:
    """Main chatbot class for handling product inquiries"""
    
    def __init__(self, products_file: str, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the chatbot with products data and OpenAI API
        
        Args:
            products_file: Path to JSON file containing product data
            api_key: OpenAI API key
            model: OpenAI model to use (default: gpt-3.5-turbo)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.products = self._load_products(products_file)
        self.user_role = UserRole.CUSTOMER
        self.conversation_history: List[Dict] = []
        self.attribute_policies = self._build_attribute_policies()
        self.system_prompt = self._create_system_prompt()
    
    def _load_products(self, products_file: str) -> List[Dict]:
        """Load and parse product data from JSON file"""
        try:
            if not os.path.exists(products_file):
                raise FileNotFoundError(f"Products file not found: {products_file}")
            
            with open(products_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get('products', [])
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            sys.exit(1)
    
    def _create_system_prompt(self) -> str:
        """
        Create system prompt that enforces scope limitation and language handling
        This is critical for restricting chatbot to product questions only
        """
        products_context = self._format_products_for_context()
        
        system_prompt = f"""You are an AI assistant for a software development company's product support chatbot. 
Your role is to answer ONLY questions related to the company's products and services.

IMPORTANT SCOPE LIMITATIONS:
1. You can ONLY answer questions about the products listed below
2. You must reject ANY questions outside the product scope (weather, politics, personal advice, homework, etc.)
3. When asked out-of-scope questions, politely decline and redirect to company products

PRODUCT DATABASE:
{products_context}

CRITICAL LANGUAGE HANDLING RULE:
⚠️ YOU MUST RESPOND IN ONLY ONE LANGUAGE:
- If user asks in ENGLISH → Respond ONLY in English (no Arabic)
- If user asks in ARABIC → Respond ONLY in Arabic (no English)
- NEVER mix languages or provide bilingual responses
- Detect the user's language from their question
- Use product names and descriptions in the response language only

RESPONSE GUIDELINES:
1. Be accurate and factual - use only information from the product database
2. For product listing: Provide comprehensive list of all products with clear formatting
3. For pricing: Always include currency (USD) in the response
4. For best seller: Calculate based on units_sold field
5. For product details: Provide name, price, category, and description in the user's language
6. If information is not in the database, say "I don't have that information about our products"
7. Format responses clearly with line breaks and bullet points when listing multiple items

OUT-OF-SCOPE REJECTION:
- English: "I can only provide information about our company's software products."
- Arabic: "يمكنني فقط تقديم معلومات عن منتجات شركتنا."

ROLE-BASED ACCESS (will be enforced separately):
- All users can ask about products
- Only staff can generate sales reports

Remember: 
1. Stay in scope
2. Use ONLY the language of the user's question
3. Keep responses well-formatted and clear"""
        
        return system_prompt
    
    def _format_products_for_context(self) -> str:
        """Format products data for AI context"""
        formatted = "Available Products:\n"
        for product in self.products:
            formatted += f"""
- ID: {product['id']}
  Name (EN): {product['name']}
  Name (AR): {product['name_ar']}
  Price: ${product['price']} {product['currency']}
  Category: {product['category']}
  Units Sold: {product['units_sold']}
  Description (EN): {product['description']}
  Description (AR): {product['description_ar']}
"""
        return formatted
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is in Arabic or English
        
        Args:
            text: User input text
            
        Returns:
            'arabic' or 'english'
        """
        # Arabic Unicode range
        arabic_count = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        english_count = sum(1 for char in text if 'a' <= char.lower() <= 'z')
        
        if arabic_count > english_count:
            return 'arabic'
        return 'english'

    def _build_attribute_policies(self) -> Dict[str, Dict]:
        """Define which product attributes are staff-only and their trigger keywords."""
        return {
            "name": {"staff_only": False, "keywords": ["name", "called", "product"]},
            "description": {"staff_only": False, "keywords": ["description", "details", "about"]},
            "category": {"staff_only": False, "keywords": ["category", "type", "segment", "kind"]},
            "price": {"staff_only": False, "keywords": ["price", "cost", "how much", "usd", "dollar"]},
            # Staff-protected attributes
            "units_sold": {
                "staff_only": True,
                "keywords": [
                    "units sold", "sold units", "units", "sold", "sales volume",
                    "best seller", "top seller", "most sold", "most selling",
                    "وحدات مباعة", "الوحدات المباعة", "مباعة", "الأكثر مبيعاً", "أفضل مبيعاً"
                ],
            },
            "revenue": {
                "staff_only": True,
                "keywords": ["revenue", "total sales", "sales revenue", "earnings", "إيرادات", "الإيرادات", "المبيعات"],
            },
        }
    
    def set_user_role(self, role: str):
        """
        Set user role for permission management
        
        Args:
            role: 'customer' or 'staff'
        """
        try:
            self.user_role = UserRole(role.lower())
        except ValueError:
            print(f"Invalid role: {role}. Using 'customer' as default.")
            self.user_role = UserRole.CUSTOMER
    
    def _check_staff_only_request(self, user_message: str) -> Optional[str]:
        """
        Check if request is staff-only (e.g., sales reports)
        
        Args:
            user_message: User input
            
        Returns:
            Staff-only response if applicable, None otherwise
        """
        staff_keywords = [
            'report', 'analytics', 'revenue', 'sales', 'dashboard', 'performance',
            'تقرير', 'تقارير', 'تحليلات', 'إيرادات', 'الإيرادات', 'مبيعات', 'المبيعات'
        ]
        lower_message = user_message.lower()
        
        is_staff_request = any(keyword in lower_message for keyword in staff_keywords)
        
        if is_staff_request and self.user_role == UserRole.CUSTOMER:
            language = self.detect_language(user_message)
            if language == 'arabic':
                return "تقارير المبيعات والتحليلات متاحة فقط لموظفي الشركة. يمكنني مساعدتك بمعلومات عن المنتجات بدلاً من ذلك."
            else:
                return "Sales reports and analytics are only available to staff members. I can help you with product information instead."
        
        return None

    def _check_attribute_access(self, user_message: str) -> Optional[str]:
        """Block staff-only product attributes (e.g., units_sold) for customer role."""
        # Staff can access everything
        if self.user_role == UserRole.STAFF:
            return None
        lower_message = user_message.lower()
        for attr, policy in self.attribute_policies.items():
            if not policy.get("staff_only"):
                continue
            if any(keyword in lower_message for keyword in policy.get("keywords", [])):
                language = self.detect_language(user_message)
                if language == 'arabic':
                    return "هذه المعلومة متاحة فقط لموظفي الشركة."
                return "This information is available to staff only."
        return None
    
    def _generate_sales_report(self) -> str:
        """
        Generate sales report (staff only)
        
        Returns:
            Formatted sales report
        """
        total_revenue = sum(p['price'] * p['units_sold'] for p in self.products)
        total_units = sum(p['units_sold'] for p in self.products)
        best_seller = max(self.products, key=lambda x: x['units_sold'])
        
        report = f"""
=== SALES REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
- Total Products: {len(self.products)}
- Total Units Sold: {total_units}
- Total Revenue: ${total_revenue:,.2f}

Top Performer:
- Product: {best_seller['name']}
- Units Sold: {best_seller['units_sold']}
- Revenue: ${best_seller['price'] * best_seller['units_sold']:,.2f}

Products by Sales:
"""
        sorted_products = sorted(self.products, key=lambda x: x['units_sold'], reverse=True)
        for product in sorted_products:
            revenue = product['price'] * product['units_sold']
            report += f"\n- {product['name']}: {product['units_sold']} units (${revenue:,.2f})"
        
        return report

    def _handle_staff_analytics(self, user_message: str, language: str) -> Optional[str]:
        """Deterministic answers for staff analytics (revenue, units, best-seller)."""
        if self.user_role != UserRole.STAFF:
            return None

        lower_message = user_message.lower()
        total_revenue = sum(p['price'] * p['units_sold'] for p in self.products)
        total_units = sum(p['units_sold'] for p in self.products)
        best_seller = max(self.products, key=lambda x: x['units_sold']) if self.products else None

        def fmt_en_revenue():
            return f"Total revenue: ${total_revenue:,.2f} USD."

        def fmt_ar_revenue():
            return f"إجمالي الإيرادات: ${total_revenue:,.2f} دولار أمريكي."

        def fmt_en_units():
            return f"Total units sold: {total_units}."

        def fmt_ar_units():
            return f"إجمالي الوحدات المباعة: {total_units}."

        def fmt_en_best():
            return (
                f"Best seller: {best_seller['name']} — {best_seller['units_sold']} units "
                f"(${best_seller['price'] * best_seller['units_sold']:,.2f})."
            ) if best_seller else "No products available."

        def fmt_ar_best():
            return (
                f"أفضل منتج مبيعاً: {best_seller['name_ar']} — {best_seller['units_sold']} وحدة "
                f"(${best_seller['price'] * best_seller['units_sold']:,.2f})."
            ) if best_seller else "لا توجد منتجات متاحة."

        # Revenue queries
        revenue_keywords = ["revenue", "total revenue", "إيرادات", "الإيرادات", "إجمالي الإيرادات", "المبيعات", "إجمالي المبيعات", "تقرير المبيعات"]
        if any(keyword in lower_message for keyword in revenue_keywords):
            return fmt_en_revenue() if language == 'english' else fmt_ar_revenue()

        # Units queries
        units_keywords = [("units", "sold"), ("وحدات", "مباعة"), ("الوحدات", "المباعة")]
        if any(all(word in lower_message for word in pair) for pair in units_keywords):
            return fmt_en_units() if language == 'english' else fmt_ar_units()

        # Best seller queries
        best_seller_keywords = [
            "best seller", "top seller", "most sold", "most selling",
            "الأكثر مبيعاً", "أفضل مبيعاً", "الأكثر مبيعا", "أكثر منتج"
        ]
        if any(term in lower_message for term in best_seller_keywords):
            return fmt_en_best() if language == 'english' else fmt_ar_best()

        return None
    
    def process_message(self, user_message: str) -> str:
        """
        Process user message and generate response
        
        Args:
            user_message: User input
            
        Returns:
            AI-generated response
        """
        user_language = self.detect_language(user_message)

        # Check for staff-only requests
        role_check = self._check_staff_only_request(user_message)
        if role_check:
            return role_check

        # Check for staff-only product attributes (e.g., units sold)
        attribute_check = self._check_attribute_access(user_message)
        if attribute_check:
            return attribute_check
        
        # Check for sales report request (staff only)
        if any(keyword in user_message.lower() for keyword in ['report', 'analytics']) and self.user_role == UserRole.STAFF:
            return self._generate_sales_report()

        # Deterministic staff analytics (revenue/units/best-seller) to avoid model drift
        analytics_response = self._handle_staff_analytics(user_message, user_language)
        if analytics_response:
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": analytics_response})
            return analytics_response

        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Get response from OpenAI
            response = self._get_ai_response(
                self.system_prompt,
                user_message,
                self.conversation_history[:-1]  # Exclude the message we just added
            )

            # If the AI responded in the wrong language, ask it to restate in the correct language
            response_language = self.detect_language(response)
            if response_language != user_language:
                restate_instruction = (
                    "Respond ONLY in English. Do not include any Arabic. "
                    if user_language == 'english' else
                    "أعد الإجابة باللغة العربية فقط ولا تستخدم الإنجليزية."
                )
                response = self._get_ai_response(
                    self.system_prompt,
                    f"{restate_instruction}\nQuestion: {user_message}",
                    self.conversation_history[:-1]
                )
            
            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
        
        except Exception as e:
            error_message = f"Error communicating with AI service: {str(e)}"
            print(f"DEBUG: {error_message}", file=sys.stderr)
            return "I apologize, but I'm experiencing technical difficulties. Please try again later."
    
    def _get_ai_response(self, system_prompt: str, user_message: str, conversation_history: List[Dict]) -> str:
        """Get response from OpenAI API"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        
        return response.choices[0].message.content
    
    def reset_conversation(self):
        """Reset conversation history for new session"""
        self.conversation_history = []
    
    def get_session_info(self) -> Dict:
        """Get current session information"""
        return {
            "role": self.user_role.value,
            "messages_count": len(self.conversation_history),
            "products_available": len(self.products)
        }
