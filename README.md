# Product Information Chatbot

AI-powered bilingual chatbot for product inquiries with role-based access control.

## Features

- 🌍 **Bilingual**: English & Arabic support with auto-detection
- 🔐 **Role-Based Access**: Customer (public info) and Staff (analytics)
- 🤖 **AI-Powered**: OpenAI GPT integration
- 📊 **Staff Analytics**: Revenue reports, sales data, best-seller insights
- 🌐 **Web Interface**: Modern Streamlit UI

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application
```bash
streamlit run simple-ui.py

```

## Usage

1. Enter your OpenAI API key in the sidebar
2. Select role: **Customer** or **Staff**
3. Click "Connect to Chatbot"
4. Start asking questions!

**Example Questions:**
- "What products do you offer?"
- "What is the price of Enterprise CRM?"
- "Which product is the best seller?" (Staff only)

**Staff-Only Features:**
- Sales reports and analytics
- Revenue totals
- Units sold statistics
- Best-seller insights

## Project Structure

```
product-chatbot/
├── chatbot.py              # Core chatbot logic
├── simple-ui.py            # Web interface
├── event_automation.py     # Event-driven automation
├── products_data.json      # Product database
├── requirements.txt        # Dependencies
└── run_streamlit.sh/bat    # Launch scripts
```

## Configuration

### Role-Based Access Control

**Customer Role:**
- Product information (name, price, description)
- Category and features
- General inquiries

**Staff Role:**
- All customer features +
- Sales reports
- Revenue analytics
- Units sold data
- Best-seller insights

### Supported Languages

- English: Automatic detection and response
- Arabic (العربية): Full bilingual support

## Troubleshooting

**Missing Dependencies:**
```bash
pip install -r requirements.txt
```

**Permission Denied (macOS/Linux):**
```bash
chmod +x run_streamlit.sh
```

**Port Already in Use:**
```bash
streamlit run streamlit_app.py --server.port 8502
```

## License

MIT License
