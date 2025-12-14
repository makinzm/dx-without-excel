"""Main Streamlit application."""
import pandas as pd
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

# 設定エラーがある場合の警告表示
if manager.has_config_error():
    st.error(f"⚠️ 設定エラー: {manager.get_config_error()}")
    if st.button("設定を再読み込み"):
        manager.reload_config()
        st.rerun()

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
    "📈 データ/計算結果",
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
                        manager.create_team(
                            team_id.strip(),
                            team_name.strip(),
                            description.strip(),
                        )
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

        # データフォーマット設定の表示
        data_format_config = manager.get_team_data_format(selected_team_id)
        if data_format_config:
            st.subheader("CSV列定義")

            if "columns" in data_format_config:
                columns_df = pd.DataFrame(data_format_config["columns"])
                st.dataframe(columns_df, width="stretch")

                # 列定義の詳細表示
                with st.expander("列定義の詳細"):
                    for col in data_format_config["columns"]:
                        col_name = col["name"]
                        col_type = col["type"]
                        required = "必須" if col.get("required", True) else "任意"
                        description = col.get("description", "")

                        st.markdown(f"**{col_name}** ({col_type}) - {required}")
                        if description:
                            st.caption(description)
                        st.divider()
        else:
            st.warning("データフォーマット設定が読み込めませんでした")
    else:
        st.info("チームを選択してデータフォーマット設定を確認してください")

with tab3:
    st.header("🧮 計算ルール設定")
    if selected_team_id:
        team = manager.get_team(selected_team_id)
        st.info(f"チーム: {team.name}")

        # 計算ルール設定の表示
        calculation_rules = manager.get_team_calculation_rules(selected_team_id)
        if calculation_rules:
            st.subheader("計算式一覧")

            for i, rule in enumerate(calculation_rules):
                with st.container():
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        st.markdown(f"**{rule.name}**")
                        st.code(rule.formula, language="python")

                    with col2:
                        if rule.description:
                            st.markdown(rule.description)

                        if rule.group_by:
                            st.caption(f"グループ化: {', '.join(rule.group_by)}")

                    if i < len(calculation_rules) - 1:
                        st.divider()
        else:
            st.warning("計算ルール設定が読み込めませんでした")
    else:
        st.info("チームを選択して計算ルール設定を確認してください")

with tab4:
    st.header("📈 データ読み込みと計算結果")
    if selected_team_id:
        team = manager.get_team(selected_team_id)
        st.info(f"チーム: {team.name}")

        df = manager.load_team_data(selected_team_id)
        if df is None:
            st.warning("データの読み込みに失敗しました。設定を確認してください。")
        else:
            st.subheader("元データ")
            st.dataframe(df, use_container_width=True)

            computed = manager.compute_with_rules(selected_team_id, df)
            st.subheader("計算結果")
            st.dataframe(computed, use_container_width=True)
    else:
        st.info("チームを選択してデータを表示してください")
