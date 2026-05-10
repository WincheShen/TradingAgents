

def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_conservative_response = risk_debate_state.get("current_conservative_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""As the Neutral Risk Analyst, your role is to act as an evidence-based judge — not a mediator. After reviewing both the Aggressive and Conservative positions, you must determine which side presents stronger evidence given the current market setup. Here is the trader's decision:

{trader_decision}

Your task is NOT to split the difference or find a middle ground. Instead:
1. Identify the single strongest argument from the Aggressive Analyst and the single strongest argument from the Conservative Analyst.
2. Evaluate which argument is better supported by the data sources below.
3. Declare which side you lean toward and why, with specific evidence.
4. Only recommend a neutral/Hold-like stance when upside and downside are genuinely symmetric AND no near-term catalyst exists. If you choose Hold, you must explicitly state what data would tip you to Buy or Sell.

Data sources:
Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Current conversation history: {history}
Last response from the aggressive analyst: {current_aggressive_response}
Last response from the conservative analyst: {current_conservative_response}
If there are no responses from the other viewpoints yet, present your own argument based on the available data.

Be decisive. A judge who always rules "both sides have a point" is not useful. Ground your verdict in the risk-adjusted expected return implied by the data. Output conversationally as if you are speaking without any special formatting."""

        response = llm.invoke(prompt)

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
