import streamlit as st
from streamlit_dynamic_filters import DynamicFilters
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="Emergency Finance App", layout="wide")

category_file = "categories.json"

if "categories" not in st.session_state:
    # this ensures the file is saved and preserved in session-state
    st.session_state.categories = {
        "Uncategorised": []
    }

if os.path.exists(category_file):
    # this opens the categories file in r=readmode named f, and basically treats data like python dic
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)


def save_categories():
    # take categories created and put into file
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f, indent=4)


def categorise_transaction(df):
    # create new col in df labelling everything as categorised
    df["Category"] = "Uncategorised"
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorised" or not keywords:
            continue
        # loop through the categories, change format to lowercase and strip out blanks leading, trailing
        # loop through the df and if the term matches category, update category in df from uncat
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        for idx, row in df.iterrows():
            details = row["Narration"].lower().strip()

            #matches = list(filter(lambda x: details in x, lowered_keywords))

            matches = [item for item in lowered_keywords if item in details]
            if matches is not None and len(matches) > 0:
                df.at[idx, "Category"] = category

            # details = details[:10]
            # if details in lowered_keywords:
            #     df.at[idx, "Category"] = category
    return df


def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
#       df.fillna(0.0, inplace=True)
#       st.write(df)
        df["Amount"] = df["Balance"]
#        df["Deposit"] = df["Credit"]
        df["Date"] = pd.to_datetime(df["Transaction Date"], format="%d/%m/%Y")
        return categorise_transaction(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None


def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    keyword = keyword[:10]
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False


def main():
    st.title("JJs Budget Dashboard")

    input_file = st.file_uploader("Upload file here", type=["csv"])

    if input_file is not None:
        df = load_transactions(input_file)

        if df is not None:
            debits_df = df.loc[df["Debit"].notna()].copy()
            credits_df = df.loc[df["Credit"].notna()].copy()
            # make a spare copy of the debits df so we can have one safe, one editable
            st.session_state.debits_df = debits_df.copy()
            st.session_state.filtered_debits_df = st.session_state.debits_df

            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
            with tab1:
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()

                st.sidebar.header("Filters")
                with st.sidebar.form("filter_form"):
                    filter_start_date = st.date_input("Start Date (DD/MM/YYYY)", format="DD/MM/YYYY")
                    filter_end_date = st.date_input("End Date (DD/MM/YYYY)", format="DD/MM/YYYY")
                    filter_apply_button = st.form_submit_button("Apply Filter")
                    if filter_apply_button:
                        # Perform filtering if filters are set
                        if filter_start_date:
                            st.caption(f'Filtering by start date: :green[{filter_start_date}]')
                            #tickets_by_month = tickets_by_month[tickets_by_month['ViolationCode'] == violation_code]
                            st.session_state.filtered_debits_df = debits_df.loc[(debits_df['Date'].dt.date >= filter_start_date) & (debits_df['Date'].dt.date <= filter_end_date)]

                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.filtered_debits_df[["Date", "Narration", "Debit", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Debit": st.column_config.NumberColumn("Debit", format="%.2f AUD"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    width="stretch",
                    key="category_editor"
                )

                # Initialize with the dataframe and columns to filter
                #dynamic_filters = DynamicFilters(df, filters=['Date', 'Category'])
                # Display filters in the sidebar
                #dynamic_filters.display_filters(location='sidebar')
                # Display the resulting filtered dataframe
                #dynamic_filters.display_df()


                save_button = st.button("Apply changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.debits_df.at[idx, "Category"]:
                            continue
                        details = row["Narration"]
                        details = details[:10]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)

                st.subheader("Expense Summary")
                category_totals = st.session_state.debits_df.groupby("Category")["Debit"].sum().reset_index()
                category_totals = category_totals.sort_values("Debit", ascending=False)
                st.dataframe(
                    category_totals,
                    column_config={
                        "Debit": st.column_config.NumberColumn("Debit", format="%.2f AUD")
                    },
                    hide_index=True,
                    width='stretch'
                )

            with tab2:
                st.write(credits_df)

            # if add_button and new_category:
            #     if new_category not in st.session_state.categories:
            #         st.session_state.categories[new_category] = []
            #          save_categories()
            #         st.rerun()


main()
