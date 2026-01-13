"""
Streamlit Web Interface for Product Information Chatbot

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

# Import the chatbot
from chatbot import ProductChatbot

# Configure page
st.set_page_config(
    page_title="Product Information Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .message-box {
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        word-wrap: break-word;
        white-space: pre-wrap;
        overflow-wrap: break-word;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f1f5fe;
        border-left: 4px solid #667eea;
        line-height: 1.5;
    }
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #fafafa;
    }
    .role-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .customer-badge {
        background-color: #fff3e0;
        color: #e65100;
    }
    .staff-badge {
        background-color: #e8f5e9;
        color: #1b5e20;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
    st.session_state.messages = []
    st.session_state.api_key = ""
    st.session_state.initialized = False

if "user_role" not in st.session_state:
    st.session_state.user_role = "customer"


def load_chatbot(api_key):
    """Initialize chatbot with given API key"""
    try:
        # Validate API key format
        if not api_key.startswith("sk-"):
            st.error("❌ Invalid API key format. Must start with 'sk-' (OpenAI)")
            return None
        
        # Get products file
        products_file = Path(__file__).parent / "products_data.json"
        
        # Create chatbot instance directly
        chatbot = ProductChatbot(str(products_file), api_key)
        chatbot.set_user_role(st.session_state.user_role)
        
        return chatbot
    except Exception as e:
        st.error(f"❌ Error initializing chatbot: {str(e)}")
        return None


def get_product_info():
    """Get product information from database"""
    try:
        products_file = Path(__file__).parent / "products_data.json"
        with open(products_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('products', [])
    except:
        return []


def display_header():
    """Display page header"""
    st.markdown("""
    <div class="header">
        <h1>🤖 Product Information Chatbot</h1>
        <p>Multilingual AI assistant for product inquiries</p>
        <p>💬 English & العربية (Arabic)</p>
    </div>
    """, unsafe_allow_html=True)


def display_role_badge(role):
    """Display role badge"""
    if role == "staff":
        st.markdown(
            '<span class="role-badge staff-badge">👨‍💼 STAFF</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span class="role-badge customer-badge">👤 CUSTOMER</span>',
            unsafe_allow_html=True
        )


def display_products():
    """Display products in sidebar"""
    st.sidebar.markdown("### 📊 Available Products")
    products = get_product_info()
    
    for product in products:
        with st.sidebar.expander(f"**{product['name']}** - ${product['price']:,}"):
            st.write(f"🏷️ **Price:** ${product['price']:,} {product['currency']}")
            st.write(f"📦 **Units Sold:** {product['units_sold']}")
            st.write(f"🏢 **Category:** {product['category']}")
            st.write(f"📝 **Description:** {product['description']}")
            st.write(f"🇸🇦 **Arabic:** {product['description_ar']}")


def main():
    """Main Streamlit app"""
    display_header()
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # API Key input
        st.markdown("### 🔑 OpenAI API Key")
        api_key_input = st.text_input(
            "Enter your OpenAI API key",
            type="password",
            key="api_key_input",
            help="OpenAI key (sk-...)"
        )
        
        # Role selection
        st.markdown("### 👤 User Role")
        role = st.radio(
            "Select your role:",
            options=["customer", "staff"],
            format_func=lambda x: "👤 Customer" if x == "customer" else "👨‍💼 Staff"
        )
        st.session_state.user_role = role
        
        # Display current role
        st.markdown("### Current Role")
        display_role_badge(role)
        
        if role == "staff":
            st.success("✅ Staff reports enabled")
        else:
            st.info("ℹ️ Limited to product information")
        
        # Initialize button
        if st.button("🚀 Connect to Chatbot", use_container_width=True):
            if not api_key_input:
                st.error("❌ Please enter an API key")
            else:
                with st.spinner("Initializing chatbot..."):
                    chatbot = load_chatbot(api_key_input)
                    if chatbot:
                        st.session_state.chatbot = chatbot
                        st.session_state.initialized = True
                        st.success("✅ Chatbot initialized!")
                        st.rerun()
        
        st.divider()
        display_products()
    
    # Main chat area
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("### Status")
        if st.session_state.initialized and st.session_state.chatbot:
            st.success("🟢 Connected")
            display_role_badge(st.session_state.user_role)
        else:
            st.warning("🟡 Not Connected")
            st.info("Configure your API key and click 'Connect' to start")
    
    # Chat interface
    if st.session_state.initialized and st.session_state.chatbot:
        st.markdown("### 💬 Chat")
        
        # Display conversation history
        if st.session_state.messages:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="message-box user-message"><strong>You:</strong> {msg["content"].replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Format bot response with proper line breaks and wrapping
                    formatted_content = msg["content"].replace('\n', '<br>')
                    st.markdown(
                        f'<div class="message-box bot-message"><strong>Bot:</strong><br>{formatted_content}</div>',
                        unsafe_allow_html=True
                    )
        
        # Input area
        st.divider()
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_area(
                "Ask a question about our products:",
                placeholder="E.g., 'What products do you offer?' or 'ما هي المنتجات؟'",
                height=100,
                key="user_input"
            )
        
        with col2:
            send_button = st.button("📤 Send", use_container_width=True, key="send_btn")
            clear_button = st.button("🗑️ Clear", use_container_width=True, key="clear_btn")
        
        # Process user input
        if send_button and user_input.strip():
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Get bot response
            with st.spinner("🤔 Thinking..."):
                response = st.session_state.chatbot.process_message(user_input)
            
            # Add bot message
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
            
            st.rerun()
        
        if clear_button:
            st.session_state.messages = []
            st.session_state.chatbot.reset_conversation()
            st.success("✅ Conversation cleared")
            st.rerun()
        
        # Quick action buttons for staff
        if st.session_state.user_role == "staff":
            st.divider()
            st.markdown("### 📊 Staff Functions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📈 Generate Sales Report", use_container_width=True):
                    response = st.session_state.chatbot._generate_sales_report()
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "Generate a sales report"
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.rerun()
            
            with col2:
                if st.button("📊 Show Product Stats", use_container_width=True):
                    products = get_product_info()
                    total_revenue = sum(p['price'] * p['units_sold'] for p in products)
                    total_units = sum(p['units_sold'] for p in products)
                    
                    stats = f"""
**Sales Statistics:**
- Total Products: {len(products)}
- Total Units Sold: {total_units}
- Total Revenue: ${total_revenue:,.2f}
- Average Price: ${total_revenue/len(products):,.2f}
                    """
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": stats
                    })
                    st.rerun()
    else:
        st.info("👈 Configure your API key in the sidebar and click 'Connect to Chatbot' to start")
        
        # Show example questions
        st.markdown("### 💡 Example Questions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**English:**")
            st.code("• What products do you offer?\n• What is the price of Enterprise CRM?\n• Which product is the best seller?\n• Tell me about HR Management Solution")
        
        with col2:
            st.markdown("**Arabic:**")
            st.code("• ما هي المنتجات المتاحة؟\n• كم سعر نظام إدارة العملاء؟\n• ما هو المنتج الأكثر مبيعاً؟\n• أخبرني عن حل إدارة الموارد البشرية")


if __name__ == "__main__":
    main()
