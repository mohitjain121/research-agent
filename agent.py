
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
import os

from supabase import create_client

import uuid



load_dotenv()

model = ChatGroq(model_name="meta-llama/llama-4-scout-17b-16e-instruct")
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)


@dataclass
class TopicMemory:
    topic_id: str
    topic_name: str

    predecessors_limitations: str
    core_proposal: str
    enabling_conditions: str
    problems_solved: str
    operational_understanding: str

    progress_history: List[dict] = field(default_factory=list)
    last_updated_ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class SchemaSection(str, Enum):
    PREDECESSORS_LIMITATIONS = "predecessors_limitations"
    CORE_PROPOSAL = "core_proposal"
    ENABLING_CONDITIONS = "enabling_conditions"
    PROBLEMS_SOLVED = "problems_solved"
    OPERATIONAL_UNDERSTANDING = "operational_understanding"

@dataclass
class TopicRoutingProposal:
    article_text: str
    suggested_topic_name: str
    vertical: str
    confidence_reason: str
    source_link: str

    def summary(self) -> str:
        return f"""
TOPIC ROUTING PROPOSAL
Suggested Topic: {self.suggested_topic_name}
Vertical: {self.vertical}

WHY:
{self.confidence_reason}
"""

    def apply(self) -> None:
        topic_id = str(uuid.uuid4())
        create_topic(topic_id, self.suggested_topic_name, self.vertical)



    def to_log_payload(self) -> dict:
        return {
            "proposal_type": "topic_routing",
            "suggested_topic_name": self.suggested_topic_name,
            "vertical": self.vertical,
            "confidence_reason": self.confidence_reason,
            "source_link": self.source_link,
        }



@dataclass
class MemoryUpdateProposal:
    topic_id: str
    schema_section: SchemaSection

    old_belief: str
    new_belief: str
    why_this_matters: str
    source_link: str

    def summary(self) -> str:
        return f"""
MEMORY UPDATE PROPOSAL
Topic ID: {self.topic_id}
Section: {self.schema_section.value}

OLD:
{self.old_belief}

NEW:
{self.new_belief}

WHY:
{self.why_this_matters}
"""

    def apply(self) -> None:
        apply_memory_update_to_db(self.topic_id, self)
    
    def to_log_payload(self) -> dict:
        return {
            "proposal_type": "memory_update",
            "topic_id": self.topic_id,
            "schema_section": self.schema_section.value,
            "old_belief": self.old_belief,
            "new_belief": self.new_belief,
            "why_this_matters": self.why_this_matters,
            "source_link": self.source_link,
        }


def fetch_topics_by_vertical(vertical: str) -> List[dict]:
    response = (
        supabase
        .table("topics")
        .select("id, name, description")
        .eq("vertical", vertical)
        .execute()
    )

    if response.data is None:
        return []

    return response.data

EXISTING_TOPIC_ROUTING_PROMPT = """
You are a research router.

You will be given:
1) A list of topics (ALL from the same vertical)
2) A new article

Your task:
- Choose the SINGLE most relevant topic
- If none are clearly relevant, respond with NO_TOPIC

Rules:
- You MUST return at most one topic
- Be conservative — only choose if relevance is strong
- Do NOT invent topics
- Do NOT explain the article

Output format (follow exactly):

TOPIC_ID: <topic_id_or_NO_TOPIC>
REASON: <1 sentence justification>
"""



def parse_topic_routing_response(
    llm_text: str,
    valid_topic_ids: set
) -> Tuple[Optional[str], str]:

    topic_id = None
    reason = None

    for line in llm_text.strip().splitlines():
        if line.startswith("TOPIC_ID:"):
            topic_id = line.replace("TOPIC_ID:", "").strip()
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    if topic_id is None or reason is None:
        return None, "Invalid routing format."

    if topic_id == "NO_TOPIC":
        return None, reason

    if topic_id not in valid_topic_ids:
        return None, "Invalid topic selected."

    return topic_id, reason


def route_article_to_topic(
    article_text: str,
    vertical: str,
    model
) -> Tuple[Optional[str], str]:

    topics = fetch_topics_by_vertical(vertical)

    if not topics:
        return None, "No topics available for this vertical."

    topics_block = "\n".join([
        f"- {t['id']}: {t['name']} — {t.get('description', '')}"
        for t in topics
    ])

    prompt = EXISTING_TOPIC_ROUTING_PROMPT + f"""

Topics:
{topics_block}

Article:
{article_text}
"""

    response = model.invoke([
        SystemMessage(content="You are a careful research router."),
        HumanMessage(content=prompt)
    ])

    topic_id, reason = parse_topic_routing_response(
        response.content,
        valid_topic_ids={t["id"] for t in topics}
    )

    return topic_id, reason

NEW_TOPIC_PROMPT = """
You are organizing research topics within a single vertical.

Vertical:
{vertical}

Existing topics in this vertical:
{existing_topics}

New article:
{article_text}

Task:
- Decide whether this article clearly belongs to ONE existing topic
- If yes, respond with NO_NEW_TOPIC
- If not, propose ONE new topic name

Rules:
- Choose at most one topic
- Be conservative: only propose a new topic if necessary
- Do NOT propose multiple topics

Output format (follow exactly):

DECISION: <NO_NEW_TOPIC or NEW_TOPIC>
TOPIC_NAME: <only if NEW_TOPIC>
REASON: <1–2 sentence justification>
"""


def build_topic_update(
    article_text: str,
    vertical: str,
    existing_topics: List[str],
    source_link: str,
    model
) -> Optional[TopicRoutingProposal]:

    prompt = NEW_TOPIC_PROMPT.format(
        vertical=vertical,
        existing_topics=existing_topics,
        article_text=article_text
    )

    response = model.invoke([
        SystemMessage(content="You are a careful research organizer."),
        HumanMessage(content=prompt)
    ])

    decision = None
    topic_name = None
    reason = None

    for line in response.content.strip().splitlines():
        if line.startswith("DECISION:"):
            decision = line.replace("DECISION:", "").strip()
        elif line.startswith("TOPIC_NAME:"):
            topic_name = line.replace("TOPIC_NAME:", "").strip()
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    if decision == "NO_NEW_TOPIC":
        return None

    if decision == "NEW_TOPIC" and topic_name and reason:
        return TopicRoutingProposal(
            article_text=article_text,
            suggested_topic_name=topic_name,
            vertical=vertical,
            confidence_reason=reason,
            source_link=source_link
        )

    return None


def identify_schema_sections(article_text: str):
    """
    Decide which schema section this article most likely affects.
    Returns one SchemaSection or None.
    """
    text = article_text.lower()

    matched_sections  = []

    if "previous models" in text or "prior approaches" in text:
        matched_sections.append("predecessors_limitations")

    if "we propose" in text or "this paper introduces" in text:
        matched_sections.append("core_proposal")
    
    if "scales better" in text or "solves prior limitations" in text:
        matched_sections.append("problems_solved")
    
    if (
        "market unlocked" in text
        or "novel product" in text
        or "multiple business usecases" in text
        or "model works like this" in text
    ):
        matched_sections.append("operational_understanding")

    if not matched_sections:
        return None

    return matched_sections


SECTION_SELECTION_PROMPT = """
You are a research analyst responsible for maintaining a structured knowledge base.

Below is:
1) The current understanding of a topic, organized into fixed schema sections
2) A new article or research excerpt
3) A list of candidate schema sections identified by heuristics

Your task:
- From the candidate schema sections, choose EXACTLY ONE section that is most impacted by the new information
- If none are meaningfully impacted, respond with NO_UPDATE

Rules:
- You may ONLY choose from the provided candidate sections
- Do NOT invent new sections
- Do NOT summarize the article
- Do NOT propose memory updates
- Your justification must be 1–2 sentences and explain why this section is most impacted

Output format (follow exactly):

SECTION: <one_candidate_section_or_NO_UPDATE>
REASON: <brief justification>
"""

def parse_llm_section_response(
        llm_text: str,
        candidate_sections: List[str]
        ) -> Tuple[Optional[str], str]:
    
    """
    Parse the LLM output and validate the chosen schema section.

    Returns:
    - (section, reason) if valid
    - (None, error_message) if invalid
    """

    section = None
    reason = None

     
    lines = llm_text.strip().splitlines()

    for line in lines:
        if line.startswith("SECTION:"):
            section = line.replace("SECTION:", "").strip()
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    if section is None or reason is None:
        return None, "Invalid format: missing SECTION or REASON."
    
    if section != "NO_UPDATE" and section not in candidate_sections:
        return None, f"Invalid section '{section}' not in candidate list."
        
    return section, reason

def chosen_schema_section(
        article_text: str, 
        candidate_sections: List[str], 
        topic_memory_text: str,
        model, 
        max_retries: int = 3
        ) -> Tuple[Optional[str], str]:

    if not candidate_sections:
        return None, "No candidate sections identified by heuristics."
    
    base_prompt = SECTION_SELECTION_PROMPT + f"""

Current Topic Understanding:
{topic_memory_text}

Candidate Schema Sections:
{candidate_sections}

Article Text:
{article_text}
"""

    for attempt in range(max_retries):

        prompt = base_prompt

        if attempt > 0:
            prompt += "\nIMPORTANT: Your previous response was invalid. Follow the output format exactly."

        
        response = model.invoke([
            SystemMessage(content="You are a careful research analyst."),
            HumanMessage(content=prompt)
        ])

        section, reason = parse_llm_section_response(response.content, candidate_sections)

        if section is not None:
            return section, reason
        
    return None, "LLM failed to produce a valid schema section after retries."


SECTION_REWRITE_PROMPT = """
You are a research editor responsible for updating ONE section of a structured knowledge base.

Below is:
1) The name of the schema section to update
2) The current belief text for that section (old_belief)
3) A new article or research excerpt

Your task:
- Rewrite the section text to reflect the most accurate current understanding
- Integrate relevant new information from the article
- Preserve useful prior context unless it is contradicted or outdated

Rules:
- Output ONLY the updated section text
- Do NOT explain your reasoning
- Do NOT justify why the update matters
- Do NOT summarize the entire article
- Do NOT introduce information not present in the old belief or the article
- Keep the result concise (1–2 short paragraphs)

Output format (follow exactly):

NEW_BELIEF: <updated_section_text>

"""

def parse_new_belief(llm_text: str) -> str:
    if "NEW_BELIEF:" not in llm_text:
        raise ValueError("Invalid rewrite format")

    return llm_text.split("NEW_BELIEF:", 1)[1].strip()


def build_memory_update(
    topic_memory: TopicMemory,
    chosen_section: str,
    justification: str,
    article_text: str,
    source_link: str,
    model) -> MemoryUpdateProposal:
    """
    Construct a MemoryUpdateProposal suggesting how the topic memory should change.

    1. Map the chosen section to the corresponding schema section in topic memory.
    2. Extract the old belief from topic memory for that section
    3. Generate a new proposed belief based on article_text
       (LLM will be used later to rewrite ONLY that section)
    4. Populate and return a MemoryUpdateProposal object
    """

    old_belief = getattr(topic_memory, chosen_section)

    prompt = SECTION_REWRITE_PROMPT + f"""

Schema Section Name:
{chosen_section}

Current Belief:
{old_belief}

Article Text:
{article_text}
"""

    response = model.invoke([
            SystemMessage(content="You are a careful research editor."),
            HumanMessage(content=prompt)
        ])
    
    new_belief = parse_new_belief(response.content)
    

    return MemoryUpdateProposal(
        topic_id=topic_memory.topic_id,
        schema_section=SchemaSection(chosen_section),

        old_belief=old_belief,
        new_belief=new_belief,
        why_this_matters=justification,
        source_link=source_link
    )


def review_proposal(proposal) -> str:
    print(proposal.summary())

    options = {"1": "Approve", "2": "Reject"}
    while True:
        choice = input("Please choose 1 (Approve) or 2 (Reject): ")
        if choice in options:
            return options[choice]

def apply_proposal(proposal) -> None:
    proposal.apply()

def handle_proposal(proposal) -> None:
    decision = review_proposal(proposal)

    if decision == "Approve":
        apply_proposal(proposal)
        log_accepted_proposal(proposal)
    else:
        rejection_reason = input("Why are you rejecting this proposal? ")
        log_rejected_proposal(proposal, rejection_reason)




def log_accepted_proposal(proposal) -> None:
    payload = proposal.to_log_payload()
    payload["status"] = "accepted"
    supabase.table("accepted_proposals").insert(payload).execute()


def log_rejected_proposal(proposal, rejection_reason: str) -> None:
    payload = proposal.to_log_payload()
    payload["status"] = "rejected"
    payload["rejection_reason"] = rejection_reason
    supabase.table("rejected_proposals").insert(payload).execute()


SECTION_TO_COLUMN = {
    "predecessors_limitations": "predecessors_limitations",
    "core_proposal": "core_proposal",
    "enabling_conditions": "enabling_conditions",
    "problems_solved": "problems_solved",
    "operational_understanding": "operational_understanding",
}

def append_progress_entry(
    progress_history: List[dict],
    proposed_update: MemoryUpdateProposal
) -> List[dict]:

    new_entry = {
        "section": proposed_update.schema_section.value,
        "source": proposed_update.source_link,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return progress_history + [new_entry]


    
def apply_memory_update_to_db(
    topic_id: str,
    proposed_update: MemoryUpdateProposal
) -> None:
    
    column = SECTION_TO_COLUMN.get(proposed_update.schema_section.value)
    if not column:
        raise ValueError("Invalid schema section")

    existing_memory = load_topic_memory(topic_id)
    if existing_memory:
        updated_progress = append_progress_entry(
            existing_memory.progress_history,
            proposed_update
        )

        update_payload = {
            column: proposed_update.new_belief,
            "progress_history": updated_progress,
            "last_updated_ts": datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table("topic_memory").update(update_payload).eq("topic_id", topic_id).execute()

    else:
        raise ValueError("No Topic exists")



def create_topic(topic_id: str, topic_name: str, vertical: str) -> str:
    supabase.table("topics").insert({
        "id": topic_id,
        "name": topic_name,
        "vertical": vertical
    }).execute()


    initialize_topic_memory(topic_id)

    return topic_id

def initialize_topic_memory(topic_id: str) -> None:
    base_row = {
        "topic_id": topic_id,
        "predecessors_limitations": "Not yet researched",
        "core_proposal": "Not yet researched",
        "enabling_conditions": "Not yet researched",
        "problems_solved": "Not yet researched",
        "operational_understanding": "Not yet researched",
        "progress_history": [],
        "last_updated_ts": datetime.now(timezone.utc).isoformat()
    }

    supabase.table("topic_memory").insert(base_row).execute()



# db data fetching via supabase client and api

def load_topic_memory(topic_id: str) -> Optional[TopicMemory]:
    
    response = (
        supabase
        .table("topic_memory")
        .select("*")
        .eq("topic_id", topic_id)
        .maybe_single()
        .execute()
    )

    if response is None or response.data is None:
        return None

    data = response.data

    return TopicMemory(
        topic_id=data["topic_id"],
        topic_name=None,
        predecessors_limitations=data["predecessors_limitations"],
        core_proposal=data["core_proposal"],
        enabling_conditions=data["enabling_conditions"],
        problems_solved=data["problems_solved"],
        operational_understanding=data["operational_understanding"],
        progress_history=data.get("progress_history") or [],
        last_updated_ts=data["last_updated_ts"]
    )













# db connection - tried using supabase db connection transaction pooler but the database url was constantly throwing password authetication failed error, 
# tried debugging everything on my end but nothing solved, hence moved to using supabase client api



# def get_db_connection():
#     return psycopg.connect(
#         os.environ["DATABASE_URL"],
#         prepare_threshold=0,
#         sslmode="require"
#     )


# def load_topic_memory(topic_id: str) -> TopicMemory | None:
    
#     conn = get_db_connection()

#     try:
#         with conn.cursor(row_factory=dict_row) as cur:
#             cur.execute("SELECT * FROM topic_memory WHERE topic_id = %s", (topic_id,))
#             row = cur.fetchone()

#             if row is None:
#                 return None
            
#             return TopicMemory(
#                 topic_id=row["topic_id"],
#                 topic_name=None,  # or handle separately
#                 predecessors_limitations=row["predecessors_limitations"],
#                 core_proposal=row["core_proposal"],
#                 enabling_conditions=row["enabling_conditions"],
#                 problems_solved=row["problems_solved"],
#                 operational_understanding=row["operational_understanding"],
#                 progress_history=row["progress_history"],
#                 last_updated_ts=row["last_updated_ts"]
#             )
#     finally:
#         conn.close()    

