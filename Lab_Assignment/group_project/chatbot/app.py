# group_project/chatbot/app.py
import streamlit as st
import sys
from pathlib import Path
import time

st.set_page_config(
    page_title="RAG Chatbot - Pháp luật Ma Tuý (Agentic)", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thêm project root vào path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from src.agents import SupervisorAgent
except Exception as e:
    st.error(f"❌ Không thể import cấu trúc Agent từ thư mục src: {str(e)}")
    st.stop()

# Thiết lập Custom CSS để giao diện sang xịn mịn hơn
st.markdown("""
<style>
    .main-title {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #1E88E5;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .dashboard-card {
        background-color: rgba(30, 136, 229, 0.05);
        border-radius: 12px;
        padding: 18px;
        border: 1px solid rgba(30, 136, 229, 0.2);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        margin-bottom: 15px;
    }
    [data-theme="dark"] .dashboard-card {
        background-color: rgba(30, 136, 229, 0.1);
        border: 1px solid rgba(30, 136, 229, 0.3);
    }
    .agent-box {
        background-color: #2E3B4E;
        color: #FFFFFF;
        padding: 10px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.85rem;
        margin-top: 10px;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# Khung tiêu đề chính
st.markdown('<div class="main-title">⚖️ RAG Multi-Agent Chatbot - Pháp Luật Phòng Chống Ma Tuý</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hệ thống Multi-Agent Pattern (Supervisor-Workers) kết hợp Document Reordering & Cost Guard</div>', unsafe_allow_html=True)

# Khởi tạo các trạng thái
if "supervisor" not in st.session_state:
    st.session_state.supervisor = SupervisorAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "trigger_run" not in st.session_state:
    st.session_state.trigger_run = False

# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Cấu Hình Hệ Thống")
    st.divider()
    
    st.markdown("#### 📊 Thông số vận hành (Mock)")
    st.metric(label="Mô hình LLM", value="gpt-4o-mini")
    st.metric(label="Giới hạn gọi", value="20 req/min")
    st.metric(label="Ngân sách ngày", value="$5.00")
    
    st.divider()
    st.markdown("#### 🕵️ Các Agent đang chạy ngầm")
    st.success("🟢 **Supervisor Agent** (Định tuyến)")
    st.info("🔵 **Worker 1**: Legal Specialist (Văn bản luật)")
    st.info("🔵 **Worker 2**: News Specialist (Vụ án & Tin tức)")
    
    st.divider()
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.session_state.trigger_run = False
        st.rerun()

# ==========================================
# LAYOUT COLUMNS
# ==========================================
col_chat, col_dash = st.columns([7, 3])

# --- CỘT PHẢI: MONITOR & QUICK COMMANDS ---
with col_dash:
    st.markdown("### 📊 Agent Monitor")
    
    # Sơ đồ Multi-Agent
    st.markdown(
        """
        <div class="dashboard-card">
            <h5 style="margin-top:0;">🧠 Luồng xử lý Multi-Agent</h5>
            <p style="font-size: 0.85rem; color: #888;">
                Supervisor tự động phân loại yêu cầu:
                Câu hỏi lý thuyết chuyển tới <b>Worker 1</b>. 
                Câu hỏi về vụ án thực tế chuyển tới cả <b>Worker 1</b> & <b>Worker 2</b>.
            </p>
            <div class="agent-box">
                [Khách hàng yêu cầu]<br>
                &nbsp;&nbsp;&nbsp;&nbsp;│<br>
                &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
                [Supervisor Agent] (Phân rã tác vụ)<br>
                &nbsp;&nbsp;&nbsp;&nbsp;├──► [Worker 1: Legal Docs]<br>
                &nbsp;&nbsp;&nbsp;&nbsp;└──► [Worker 2: News & Cases]<br>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Gợi ý câu hỏi nhanh
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("<h5 style='margin-top:0;'>💡 Câu hỏi gợi ý nhanh</h5>", unsafe_allow_html=True)
    
    q1 = "Mức phạt tàng trữ ma túy là bao nhiêu?"
    q2 = "Vụ án diễn viên Hữu Tín bị xử phạt thế nào?"
    q3 = "Luật phòng chống ma túy 2021 cấm những gì?"
    
    if st.button(f"📌 {q1}", key="q1", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": q1})
        st.session_state.trigger_run = True
        st.rerun()
        
    if st.button(f"📌 {q2}", key="q2", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": q2})
        st.session_state.trigger_run = True
        st.rerun()
        
    if st.button(f"📌 {q3}", key="q3", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": q3})
        st.session_state.trigger_run = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- CỘT TRÁI: CHAT SYSTEM ---
with col_chat:
    st.markdown("### 💬 Trò chuyện với Agent")
    
    # Phân chia Tab Chat và Logs hệ thống
    tab_chat, tab_logs = st.tabs(["💬 Khung Hội Thoại", "🔬 Logs Quy Trình Agent"])
    
    with tab_chat:
        # In lịch sử chat
        for message in st.session_state.messages:
            avatar = "👤" if message["role"] == "user" else "⚖️"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
                
                # In thông tin Agent đã sử dụng và trích nguồn
                if "workflow_steps" in message and message["workflow_steps"]:
                    with st.expander("🔍 Xem lại chi tiết vết tư duy và tài liệu trích dẫn của Agent"):
                        sub_think, sub_src = st.tabs(["🕵️ Nhật ký điều phối", "📚 Ngữ cảnh trích nguồn"])
                        
                        with sub_think:
                            for step in message["workflow_steps"]:
                                st.markdown(f"**{step['title']}**")
                                step_log = step["log"].replace('\n', ' | ')
                                st.code(step_log, language="text")
                                
                        with sub_src:
                            if "sources" in message and message["sources"]:
                                for i, doc in enumerate(message["sources"], 1):
                                    meta = doc.get("metadata", {})
                                    st.markdown(f"**[{i}] Nguồn: {meta.get('source', 'Tài liệu')}** | Phân loại: `{meta.get('doc_type', 'unknown').upper()}`")
                                    st.info(doc.get("content"))
                            else:
                                st.info("Không có tài liệu trích nguồn trực tiếp.")

        # Ô nhập liệu
        prompt = st.chat_input("Nhập câu hỏi của bạn tại đây...")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.trigger_run = True
            st.rerun()

        # Thực thi xử lý khi có tin nhắn mới
        if st.session_state.trigger_run and st.session_state.messages:
            st.session_state.trigger_run = False
            user_msg = st.session_state.messages[-1]
            history = st.session_state.messages[:-1]
            
            with st.chat_message("assistant", avatar="⚖️"):
                # Hiển thị luồng chạy ngầm của Agent
                with st.status("🕵️ Supervisor đang phân tách yêu cầu và triệu tập các Worker...", expanded=True) as status:
                    result = st.session_state.supervisor.route_and_execute(query=user_msg["content"], chat_history=history)
                    
                    # Giả lập in tiến trình thực thi trực quan
                    for step in result.get("workflow_steps", []):
                        st.write(step["title"])
                        step_log = step["log"].replace('\n', ' | ')
                        st.caption(f"_{step_log}_")
                        time.sleep(0.2)
                    
                    status.update(label="✅ Toàn bộ các Agent đã xử lý xong thông tin!", state="complete", expanded=False)
                
                # Hiển thị kết quả trả về
                answer = result.get("answer")
                sources = result.get("sources", [])
                
                st.markdown(answer)
                
                # Lưu vào lịch sử chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "workflow_steps": result.get("workflow_steps", []),
                    "sources": sources
                })
                st.rerun()

    with tab_logs:
        # Logs chi tiết phiên làm việc cuối
        if st.session_state.messages:
            latest_assistant = next((m for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None)
            if latest_assistant:
                st.markdown("#### 📝 Lịch trình thực thi của hệ thống Agent cho câu hỏi vừa rồi:")
                for step in latest_assistant["workflow_steps"]:
                    st.markdown(f"##### {step['title']}")
                    st.info(step["log"])
            else:
                st.info("Chưa ghi nhận logs. Hãy đặt câu hỏi trước.")
        else:
            st.info("Khung logs trống. Vui lòng gửi câu hỏi để ghi nhận vết hoạt động của Agent.")