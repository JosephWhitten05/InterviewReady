import json
from pathlib import Path

import pandas as pd
import streamlit as st

from coach import (CRITERIA, CoachError, check_answer, check_posting,
                   generate_questions, grade_answer)

SAMPLE_POSTING = Path("data/sample_posting.txt")
DEMO_FILE = Path("data/demo_session.json")

st.set_page_config(page_title="InterviewReady", layout="wide")
ss = st.session_state
for key, default in (("posting", ""), ("role_title", ""), ("questions", []),
                     ("attempts", [])):
    ss.setdefault(key, default)


def load_sample():
    ss.posting = SAMPLE_POSTING.read_text(encoding="utf-8")


def load_demo():
    demo = json.loads(DEMO_FILE.read_text(encoding="utf-8"))
    ss.posting = demo["posting"]
    ss.role_title = demo["role_title"]
    ss.questions = demo["questions"]
    ss.attempts = demo["attempts"]


def save_demo():  # developer helper: run it once to create the offline demo
    DEMO_FILE.parent.mkdir(exist_ok=True)
    DEMO_FILE.write_text(json.dumps({
        "posting": ss.posting, "role_title": ss.role_title,
        "questions": ss.questions, "attempts": ss.attempts}, indent=2),
        encoding="utf-8")


def reset():
    ss.posting, ss.role_title, ss.questions, ss.attempts = "", "", [], []


with st.sidebar:
    st.header("Demo helpers")
    st.button("Load sample job posting", on_click=load_sample,
              disabled=not SAMPLE_POSTING.exists())
    st.button("Load saved demo session", on_click=load_demo,
              disabled=not DEMO_FILE.exists())
    st.button("Save session as demo (dev)", on_click=save_demo)
    st.button("Start over", on_click=reset)
    st.caption("Privacy: nothing is stored on a server. Your text is sent to an AI "
               "service to produce feedback, so do not paste personal or "
               "confidential details.")

st.title("InterviewReady")
st.caption("Free interview practice: paste a job posting, answer role-specific "
           "questions, get scored feedback.")

# ---- Step 1: posting and questions ----
st.subheader("1. Paste a job posting")
st.text_area("Job posting", key="posting", height=200)
num_q = st.slider("Number of questions", 3, 5, 3)
if st.button("Generate questions", type="primary"):
    problem = check_posting(ss.posting)
    if problem:
        st.error(problem)
    else:
        with st.spinner("Reading the posting..."):
            try:
                data = generate_questions(ss.posting, num_q)
                ss.role_title = data.get("role_title", "")
                ss.questions = data["questions"]
                ss.attempts = []
            except CoachError as exc:
                st.error("Could not generate valid questions: " + "; ".join(exc.errors))
            except Exception as exc:  # network, key, quota
                st.error(f"Could not reach the AI service ({exc}). Use 'Load saved demo session'.")

if not ss.questions:
    st.stop()


#--- Step 2: ---
st.subheader(f"2. Practice: {ss.role_title}" if ss.role_title else "2. Practice")
labels = [f"Q{i}: {q['question']}" for i, q in enumerate(ss.questions, start=1)]
choice = st.radio("Pick a question", range(len(labels)), format_func=lambda i: labels[i])
q = ss.questions[choice]
with st.expander("What interviewers look for"):
    st.write(q.get("what_they_look_for", ""))
answer = st.text_area("Your answer (about 90 seconds, 150 to 250 words)", key=f"answer-{choice}", height=200)

if st.button("Get feedback"):
    problem = check_answer(answer)
    if problem:
        st.error(problem)
    else:
        with st.spinner("Scoring your answer..."):
            try:
                fb = grade_answer(ss.posting, q["question"], q.get("what_they_look_for", ""), answer)
                n = sum(1 for a in ss.attempts if a["question_index"] == choice) + 1
                ss.attempts.append({"question_index": choice, "attempt": n, "answer": answer, **fb})
            except CoachError as exc:
                st.error("Could not produce valid feedback: " + "; ".join(exc.errors))
            except Exception as exc:
                st.error(f"Could not reach the AI service ({exc}). Use 'Load saved demo session'.")


# --- Step 3 ---
mine = [a for a in ss.attempts if a["question_index"] == choice]
if mine:
    last = mine[-1]
    prev = mine[-2] if len(mine) > 1 else None
    st.subheader(f"3. Feedback (attempt {last['attempt']})")
    cols = st.columns(5)
    for col, c in zip(cols, CRITERIA):
        delta = last["scores"][c] - prev["scores"][c] if prev else None
        col.metric(c.capitalize(), f"{last['scores'][c]}/5", delta =delta)
    delta = round(last["overall"] - prev["overall"], 1) if prev else None
    cols[4].metric("Overall", f"{last['overall']}/5", delta=delta)
    st.success("Strength: " + last["strength"])
    st.markdown("**Two things to improve**")
    for s in last["suggestions"]:
        st.markdown("- " + s)
    with st.expander("See a stronger example answer"):
        st.write(last["improved_answer"])
        st.caption("Built only from your own facts. Replace [bracketed] placeholders with real " 
                   "details, and never claim experience you do not have.")
        if prev: 
            st.line_chart(pd.DataFrame({"Overall score": [a["overall"] for a in mine]},
                                       index=[a["attempt"] for a in mine]))


# --- Step 4 ---

if ss.attempts:
    st.subheader("Session progress")
    df = pd.DataFrame([{"Question": a["question_index"] + 1, "attempt": a["attempt"],
                        **a["scores"], "Overall": a["overall"]} for a in ss.attempts])
    st.dataframe(df, hide_index=True)
    st.caption("Average score by criterion")
    st.bar_chart(df[CRITERIA].mean())
                 


