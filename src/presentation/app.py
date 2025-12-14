"""Main Streamlit application."""
import streamlit as st

from src.presentation.team_manager import TeamManager

st.set_page_config(
    page_title="Excel DX 設定管理",
    page_icon="📊",
    layout="wide",
)

# TeamManagerの初期化
if "team_manager" not in st.session_state:
    st.session_state.team_manager = TeamManager()

manager = st.session_state.team_manager

# サイドバー
st.sidebar.title("🏢 チーム選択")

teams = manager.get_all_teams()
if teams:
    team_options = {tid: team.name for tid, team in teams.items()}
    selected_team_id = st.sidebar.selectbox(
        "チームを選択",
        options=list(team_options.keys()),
        format_func=lambda x: team_options[x],
        key="team_selector",
    )
else:
    selected_team_id = None
    st.sidebar.info("チームが登録されていません")

if st.sidebar.button("+ 新規チーム作成", key="create_team_button"):
    st.session_state.show_create_form = True

st.sidebar.divider()
st.sidebar.caption("v0.1.0 - Sprint 1")

# メインエリア
st.title("📊 Excel DX 設定管理システム")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 チーム設定",
    "📊 データフォーマット",
    "🧮 計算ルール",
    "🔄 Git連携",
])

with tab1:
    if st.session_state.get("show_create_form", False):
        st.header("新規チーム作成")

        with st.form("create_team_form"):
            team_id = st.text_input("チームID *", placeholder="team_c")
            team_name = st.text_input("チーム名 *", placeholder="営業チームC")
            description = st.text_area("説明", placeholder="このチームの説明")

            col_submit, col_cancel = st.columns([1, 4])

            with col_submit:
                submitted = st.form_submit_button("💾 保存", type="primary")

            with col_cancel:
                cancelled = st.form_submit_button("❌ キャンセル")

            if submitted:
                # 入力値の検証
                if not team_id.strip() or not team_name.strip():
                    st.error("チームIDとチーム名は必須です")
                else:
                    try:
                        manager.create_team(team_id.strip(), team_name.strip(), description.strip())
                        st.success(f"✅ チーム '{team_name.strip()}' を作成しました")
                        st.session_state.show_create_form = False
                    except ValueError as e:
                        st.error(str(e))

            if cancelled:
                st.session_state.show_create_form = False
                st.rerun()

    elif selected_team_id:
        team = manager.get_team(selected_team_id)
        st.header(f"📋 {team.name}")

        if team.description:
            st.info(team.description)

        st.subheader("基本情報")
        st.write(f"**チームID**: `{team.id}`")

    else:
        st.info("👈 サイドバーから「新規チーム作成」を選択してください")

with tab2:
    st.header("📊 データフォーマット設定")
    if selected_team_id:
        team = manager.get_team(selected_team_id)
        st.info(f"チーム: {team.name}")
    st.write("TODO: データフォーマット設定機能")

with tab3:
    st.header("🧮 計算ルール設定")
    if selected_team_id:
        team = manager.get_team(selected_team_id)
        st.info(f"チーム: {team.name}")
    st.write("TODO: 計算ルール設定機能")

with tab4:
    st.header("🔄 Git連携")
    st.write("TODO: Git連携機能")
