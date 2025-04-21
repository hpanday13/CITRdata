import streamlit as st
import pandas as pd
import jsonlines
import os
import altair as alt

st.set_page_config(page_title="CITR LibGen Review", layout="wide")

st.title("📚 CITR Member Publication Review from LibGen")

jsonl_path = "libgen_results.jsonl"

if not os.path.exists(jsonl_path):
    st.error("No data found. Please make sure 'libgen_results.jsonl' exists in the app directory.")
    st.stop()

# Load JSONL file
data = []
with jsonlines.open(jsonl_path) as reader:
    for obj in reader:
        if "results" in obj:
            for r in obj["results"]:
                r["CITR member"] = obj["CITR member"]
                data.append(r)
        else:
            continue

df = pd.DataFrame(data)

# --- STATISTICS ---
st.subheader("📈 Summary Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Members Matched", df['CITR member'].nunique())
with col2:
    st.metric("Total Publications Found", len(df))
with col3:
    st.metric("Unique Titles", df['title'].nunique())

# More visualizations
st.markdown("### 📊 Distribution of Publications by Year")
year_chart = alt.Chart(df[df['year'].str.isnumeric()]).mark_bar().encode(
    x=alt.X('year:N', sort='-x', title='Publication Year'),
    y=alt.Y('count()', title='Number of Publications'),
    tooltip=['year', 'count()']
).properties(height=300)
st.altair_chart(year_chart, use_container_width=True)

st.markdown("### 📚 Most Common Languages")
language_chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('count()', title='Number of Publications'),
    y=alt.Y('language:N', sort='-x', title='Language'),
    tooltip=['language', 'count()']
).properties(height=300)
st.altair_chart(language_chart, use_container_width=True)

# Show full dataset
with st.expander("📄 View Entire Dataset"):
    st.dataframe(df, use_container_width=True)

# Filter by member with search
search_term = st.text_input("Search for a CITR member:")
filtered_members = sorted([m for m in df['CITR member'].unique() if search_term.lower() in m.lower()])
if not filtered_members:
    st.warning("No matching members found.")
    st.stop()
selected_member = st.selectbox("Select a CITR Member", filtered_members)
member_df = df[df['CITR member'] == selected_member].reset_index(drop=True)

st.markdown(f"### Publications Found for **{selected_member}**")

# Editable table for member publications
edited_df = st.data_editor(
    member_df.drop(columns=["CITR member"]),
    num_rows="dynamic",
    use_container_width=True,
    key="data_editor"
)

if st.button("💾 Save Changes"):
    # Replace old entries with the updated DataFrame
    df = df[df['CITR member'] != selected_member]
    edited_df['CITR member'] = selected_member
    df = pd.concat([df, edited_df], ignore_index=True)
    with jsonlines.open(jsonl_path, mode='w') as writer:
        grouped = df.groupby('CITR member')
        for name, group in grouped:
            results = group.drop(columns=['CITR member']).to_dict(orient='records')
            writer.write({"CITR member": name, "num_results": len(results), "results": results})
    st.success("Changes saved successfully.")
    st.experimental_rerun()
