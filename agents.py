import os
import json
from openai import OpenAI
from tools import search_web, search_news
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_research_agent(company: str) -> tuple:
    results = search_web(f"{company} company overview business model")
    context = "\n".join([f"[{i+1}] {r['title']}: {r['snippet']} (source: {r['link']})" for i, r in enumerate(results)])
    sources = [{"title": r["title"], "link": r["link"]} for r in results]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a research analyst writing for a general business audience. Write like a smart journalist: clear, confident, direct. No bullet points. No corporate jargon. No em dashes. No hyphens used as dashes. Summarize what this company does, how they make money, and where they sit in their market in two to three sentences. After every sentence that uses information from a source, place a citation marker in this exact format: {{1}} or {{2}} matching the source number. Every factual claim must have a citation. If search results contain multiple companies with similar names, identify the most prominent one and note any ambiguity."""
            },
            {
                "role": "user",
                "content": f"Company: {company}\n\nSearch Results:\n{context}"
            }
        ]
    )
    return response.choices[0].message.content, sources


def run_news_agent(company: str) -> tuple:
    results = search_news(f"{company} latest news 2025")
    context = "\n".join([f"[{i+1}] [{r.get('date', 'recent')}] {r['title']}: {r['snippet']} (source: {r['link']})" for i, r in enumerate(results)])
    sources = [{"title": r["title"], "link": r["link"], "date": r.get("date", "")} for r in results]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a news analyst writing for a smart but non-technical reader. Write like a senior reporter: punchy, specific, no fluff. No em dashes. No hyphens used as dashes. Summarize the three to five most important recent developments for this company in plain prose, not bullet points. After every sentence that uses information from a source, place a citation marker in this exact format: {{1}} or {{2}} matching the source number. Every factual claim must have a citation. Focus on what actually matters: deals, leadership changes, controversies, expansions, financials. Skip anything generic or PR-sounding."""
            },
            {
                "role": "user",
                "content": f"Company: {company}\n\nRecent News:\n{context}"
            }
        ]
    )
    return response.choices[0].message.content, sources


def run_sentiment_agent(company: str, news_summary: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a straight-talking risk analyst. No hedging, no corporate softening, no em dashes, no hyphens used as dashes. Given a news summary, tell the reader the overall vibe around this company right now, what could hurt them, and what is working in their favor. Write it like you are briefing a busy executive who has thirty seconds. Plain English. Two to four sentences total. End with a risk rating from 1 to 10 and one sentence explaining it."""
            },
            {
                "role": "user",
                "content": f"Company: {company}\n\nNews Summary:\n{news_summary}"
            }
        ]
    )
    return response.choices[0].message.content


def run_synthesis_agent(company: str, research: str, news: str, sentiment: str, all_sources: list) -> str:
    sources_indexed = "\n".join([f"[{i+1}] {s['title']}: {s['link']}" for i, s in enumerate(all_sources)])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a senior intelligence analyst writing a brief that a CEO would actually read.
Write like a human being: clear, direct, a little personality. No corporate speak. No filler. No em dashes. No hyphens used as dashes anywhere in your response.

You have a numbered list of sources. You MUST place a citation marker after EVERY single bullet point and every sentence without exception, using this exact format: {{1}} or {{2}} matching the source number. Every piece of information must be attributed. If multiple sources support a point, stack them like {{1}}{{3}}. No bullet point or sentence should ever appear without at least one citation marker. ATLEAST 3 citations mimimum through different sites unless there is absolutely none, should be provided during research of any company or brand. If you don't have information to support a section, say so clearly. Never make assumptions or use information that isn't in the sources. If sources conflict, note the disagreement and cite them all. BUT CITATION IS IMPORTANT.

Use this exact structure:

## Company Overview
Three to four bullet points. What they do, how they make money, their market position, one standout fact. Each bullet is one clear sentence followed immediately by its citation marker.

## Recent Developments
Four to five bullet points. Each is one to two sentences covering a specific recent event: a deal, a launch, a financial result, a leadership move, a controversy. Each bullet must end with a citation marker.

## Sentiment & Risk
Three to four bullet points. Cover: overall market sentiment, the biggest risk, the biggest opportunity, and the risk rating. Format the last bullet as: Risk Rating: X/10 and one sentence reason. Each bullet must end with a citation marker.

## Strategic Signals
Three to four bullet points. What is this company signaling about their direction? Expanding, consolidating, pivoting, struggling? Be specific. Each bullet must end with a citation marker.

## Analyst Verdict
Two to three sentences of flowing prose only. No bullets. Your honest bottom line. Write it like you are telling a sharp friend who is about to make a business decision involving this company. Add citation markers where relevant.

## Sources
List each source as: [Title](URL)

If the company name is invalid or unrecognizable, say so clearly in plain English in the overview section only and skip the remaining sections."""
            },
            {
                "role": "user",
                "content": f"Company: {company}\n\nResearch:\n{research}\n\nNews:\n{news}\n\nSentiment:\n{sentiment}\n\nSources:\n{sources_indexed}"
            }
        ]
    )
    return response.choices[0].message.content


def run_orchestrator(company: str):
    yield f"data: {json.dumps({'agent': 'Orchestrator', 'status': 'starting', 'message': f'Initializing intelligence pipeline for {company}...'})}\n\n"

    yield f"data: {json.dumps({'agent': 'Research Agent', 'status': 'running', 'message': 'Searching company overview and business model...'})}\n\n"
    research, research_sources = run_research_agent(company)
    yield f"data: {json.dumps({'agent': 'Research Agent', 'status': 'done', 'message': research})}\n\n"

    yield f"data: {json.dumps({'agent': 'News Agent', 'status': 'running', 'message': 'Scanning recent news and developments...'})}\n\n"
    news, news_sources = run_news_agent(company)
    yield f"data: {json.dumps({'agent': 'News Agent', 'status': 'done', 'message': news})}\n\n"

    yield f"data: {json.dumps({'agent': 'Sentiment Agent', 'status': 'running', 'message': 'Analyzing sentiment and risk signals...'})}\n\n"
    sentiment = run_sentiment_agent(company, news)
    yield f"data: {json.dumps({'agent': 'Sentiment Agent', 'status': 'done', 'message': sentiment})}\n\n"

    all_sources = research_sources + news_sources

    yield f"data: {json.dumps({'agent': 'Synthesis Agent', 'status': 'running', 'message': 'Compiling final intelligence brief...'})}\n\n"
    brief = run_synthesis_agent(company, research, news, sentiment, all_sources)
    yield f"data: {json.dumps({'agent': 'Synthesis Agent', 'status': 'done', 'message': brief})}\n\n"

    yield f"data: {json.dumps({'agent': 'Orchestrator', 'status': 'complete', 'message': 'Intelligence brief complete.'})}\n\n"