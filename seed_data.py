"""
Generate realistic seed data for AgentIQ MVP
Creates 500 agent interaction sessions across 5 intent types:
- billing, refunds, subscriptions, account recovery, general enquiry
"""

import random
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Intent type distributions and characteristics
INTENT_TYPES = {
    "billing": {
        "weight": 0.25,
        "avg_interactions": 4,
        "completion_rate": 0.75,
        "complexity": "medium",
        "typical_tools": ["billing_api", "payment_processor", "invoice_generator"],
        "user_queries": [
            "I have a question about my last bill",
            "My payment didn't go through, can you help?",
            "I see a charge I don't recognize",
            "Can you explain this billing cycle?",
            "I need to update my payment method"
        ]
    },
    "refunds": {
        "weight": 0.20,
        "avg_interactions": 6,
        "completion_rate": 0.60,
        "complexity": "high",
        "typical_tools": ["refund_api", "order_lookup", "policy_checker"],
        "user_queries": [
            "I want to return this product",
            "How do I get a refund for my order?",
            "The item I received is damaged",
            "I changed my mind about my purchase",
            "When will my refund be processed?"
        ]
    },
    "subscriptions": {
        "weight": 0.25,
        "avg_interactions": 3,
        "completion_rate": 0.85,
        "complexity": "low",
        "typical_tools": ["subscription_api", "plan_manager", "billing_api"],
        "user_queries": [
            "How do I cancel my subscription?",
            "I want to upgrade my plan",
            "When is my next billing date?",
            "Can I pause my subscription temporarily?",
            "What's included in the premium plan?"
        ]
    },
    "account_recovery": {
        "weight": 0.15,
        "avg_interactions": 5,
        "completion_rate": 0.70,
        "complexity": "high",
        "typical_tools": ["auth_api", "identity_verifier", "password_reset"],
        "user_queries": [
            "I can't access my account",
            "I forgot my password",
            "Someone might have hacked my account",
            "I need to reset my two-factor authentication",
            "My email address changed, how do I update it?"
        ]
    },
    "general_enquiry": {
        "weight": 0.15,
        "avg_interactions": 2,
        "completion_rate": 0.90,
        "complexity": "low",
        "typical_tools": ["knowledge_base", "faq_search"],
        "user_queries": [
            "What are your business hours?",
            "Do you offer customer support in other languages?",
            "How can I contact a human representative?",
            "What's your return policy?",
            "Do you have a mobile app?"
        ]
    }
}

def generate_agent_responses(intent: str, user_input: str, workflow_step: int) -> Dict[str, Any]:
    """Generate realistic agent responses based on intent and workflow step"""
    
    base_responses = {
        "billing": [
            "I can help you with your billing question. Let me look up your account details.",
            "I see the charge you're referring to. Let me explain what this covers.",
            "I've found the issue with your payment method. Here's what we can do to fix it.",
            "Your billing cycle runs from the 1st to the 30th of each month."
        ],
        "refunds": [
            "I understand you'd like to process a return. Let me check your order details.",
            "I see your order is eligible for a refund. Let me start the process for you.",
            "The refund has been initiated and should appear in your account within 3-5 business days.",
            "Unfortunately, this item is outside our return window, but let me see what options we have."
        ],
        "subscriptions": [
            "I can help you manage your subscription. What would you like to do?",
            "Your subscription is currently active and will renew on the 15th of next month.",
            "I've successfully updated your plan. The changes will take effect immediately.",
            "Your subscription has been cancelled. You'll retain access until your current billing period ends."
        ],
        "account_recovery": [
            "I'll help you regain access to your account. For security, I need to verify your identity first.",
            "I've sent a password reset link to your registered email address.",
            "I see there's been unusual activity on your account. Let me secure it for you.",
            "Two-factor authentication has been reset. Please set it up again using the app."
        ],
        "general_enquiry": [
            "I'm happy to answer your question! Our customer support is available 24/7.",
            "You can find detailed information about this in our help center.",
            "I've found the answer to your question in our knowledge base.",
            "For complex issues like this, I recommend speaking with one of our specialists."
        ]
    }
    
    response_text = random.choice(base_responses[intent])
    
    # Simulate tool calls based on intent
    tools_used = []
    if workflow_step <= 2:  # Early steps more likely to use tools
        if random.random() < 0.7:  # 70% chance of tool use
            intent_tools = INTENT_TYPES[intent]["typical_tools"]
            tools_used = random.sample(intent_tools, min(2, len(intent_tools)))
    
    # Response time varies by complexity and tool usage
    base_time = {"low": 800, "medium": 1200, "high": 2000}[INTENT_TYPES[intent]["complexity"]]
    tool_overhead = len(tools_used) * 400
    response_time = base_time + tool_overhead + random.randint(-200, 500)
    
    return {
        "response_text": response_text,
        "tools_used": tools_used,
        "response_time_ms": max(300, response_time),  # Minimum 300ms
        "tokens_used": random.randint(50, 200)
    }

def simulate_session_quality(intent: str, interactions: List[Dict]) -> float:
    """Calculate overall session success score based on various factors"""
    base_score = INTENT_TYPES[intent]["completion_rate"]
    
    # Adjust based on session length
    optimal_length = INTENT_TYPES[intent]["avg_interactions"]
    length_penalty = abs(len(interactions) - optimal_length) * 0.05
    
    # Adjust based on errors
    error_count = sum(1 for i in interactions if i.get("error_occurred", False))
    error_penalty = error_count * 0.15
    
    # Adjust based on response times (penalize very slow responses)
    avg_response_time = sum(i["response_time_ms"] for i in interactions) / len(interactions)
    time_penalty = max(0, (avg_response_time - 2000) / 1000 * 0.1)
    
    final_score = max(0.0, min(1.0, base_score - length_penalty - error_penalty - time_penalty))
    return round(final_score, 2)

def generate_session_data() -> List[Dict[str, Any]]:
    """Generate all session data for 500 realistic agent interactions"""
    sessions = []
    
    # Generate sessions based on intent distribution
    for intent, config in INTENT_TYPES.items():
        session_count = int(500 * config["weight"])
        
        for _ in range(session_count):
            session_id = str(uuid.uuid4())
            
            # Determine session characteristics
            num_interactions = max(1, int(random.gauss(config["avg_interactions"], 1.5)))
            session_start = datetime.now() - timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            session_interactions = []
            current_time = session_start
            
            # Generate each interaction in the session
            for step in range(1, num_interactions + 1):
                user_input = random.choice(config["user_queries"])
                
                # Generate agent response
                response_data = generate_agent_responses(intent, user_input, step)
                
                # Simulate occasional errors (5% chance, higher for complex intents)
                error_chance = 0.05 if config["complexity"] != "high" else 0.10
                has_error = random.random() < error_chance
                
                interaction = {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "timestamp": current_time,
                    "user_input": user_input,
                    "agent_response": response_data["response_text"],
                    "intent": intent,
                    "workflow_step": step,
                    "tool_calls": json.dumps(response_data["tools_used"]) if response_data["tools_used"] else None,
                    "response_time_ms": response_data["response_time_ms"],
                    "tokens_used": response_data["tokens_used"],
                    "error_occurred": has_error,
                    "error_message": "API timeout error" if has_error else None
                }
                
                session_interactions.append(interaction)
                current_time += timedelta(minutes=random.randint(1, 5))
            
            # Determine if session completed successfully
            completion_chance = config["completion_rate"]
            # Reduce completion chance if there were errors
            if any(i["error_occurred"] for i in session_interactions):
                completion_chance *= 0.7
            
            completed = random.random() < completion_chance
            drop_off_step = None if completed else random.randint(1, len(session_interactions))
            
            # Calculate session metrics
            total_tokens = sum(i["tokens_used"] for i in session_interactions)
            avg_response_time = sum(i["response_time_ms"] for i in session_interactions) / len(session_interactions)
            errors_count = sum(1 for i in session_interactions if i["error_occurred"])
            success_score = simulate_session_quality(intent, session_interactions)
            
            session_summary = {
                "id": session_id,
                "started_at": session_start,
                "ended_at": current_time,
                "duration_seconds": int((current_time - session_start).total_seconds()),
                "total_interactions": len(session_interactions),
                "primary_intent": intent,
                "intent_confidence": round(random.uniform(0.75, 0.95), 2),
                "workflow_completed": completed,
                "drop_off_step": drop_off_step,
                "total_tokens": total_tokens,
                "avg_response_time_ms": round(avg_response_time, 1),
                "errors_count": errors_count,
                "success_score": success_score
            }
            
            sessions.append({
                "summary": session_summary,
                "interactions": session_interactions
            })
    
    return sessions

def insert_seed_data():
    """Insert generated seed data into the database"""
    
    print("🌱 Generating 500 realistic agent interaction sessions...")
    sessions_data = generate_session_data()
    
    print(f"📊 Generated {len(sessions_data)} sessions with intent distribution:")
    intent_counts = {}
    for session in sessions_data:
        intent = session["summary"]["primary_intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    for intent, count in intent_counts.items():
        print(f"   {intent}: {count} sessions")
    
    # Connect to database
    conn = sqlite3.connect("agentiq.db")
    cursor = conn.cursor()
    
    try:
        print("\n💾 Inserting session summaries...")
        for session in sessions_data:
            summary = session["summary"]
            cursor.execute("""
                INSERT INTO session_summaries 
                (id, started_at, ended_at, duration_seconds, total_interactions,
                 primary_intent, intent_confidence, workflow_completed, drop_off_step,
                 total_tokens, avg_response_time_ms, errors_count, success_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                summary["id"], summary["started_at"], summary["ended_at"],
                summary["duration_seconds"], summary["total_interactions"],
                summary["primary_intent"], summary["intent_confidence"],
                summary["workflow_completed"], summary["drop_off_step"],
                summary["total_tokens"], summary["avg_response_time_ms"],
                summary["errors_count"], summary["success_score"]
            ))
        
        print("💬 Inserting agent interaction logs...")
        for session in sessions_data:
            for interaction in session["interactions"]:
                cursor.execute("""
                    INSERT INTO agent_logs 
                    (id, session_id, timestamp, user_input, agent_response,
                     intent, workflow_step, tool_calls, response_time_ms,
                     tokens_used, error_occurred, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    interaction["id"], interaction["session_id"], interaction["timestamp"],
                    interaction["user_input"], interaction["agent_response"],
                    interaction["intent"], interaction["workflow_step"],
                    interaction["tool_calls"], interaction["response_time_ms"],
                    interaction["tokens_used"], interaction["error_occurred"],
                    interaction["error_message"]
                ))
        
        conn.commit()
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM session_summaries")
        session_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_logs")
        log_count = cursor.fetchone()[0]
        
        print(f"\n✅ Seed data inserted successfully!")
        print(f"   📈 {session_count} session summaries")
        print(f"   💭 {log_count} agent interaction logs")
        print(f"   🎯 {len(INTENT_TYPES)} intent types: {', '.join(INTENT_TYPES.keys())}")
        
        # Show some sample stats
        cursor.execute("""
            SELECT primary_intent, 
                   COUNT(*) as sessions,
                   AVG(success_score) as avg_success,
                   AVG(total_interactions) as avg_interactions,
                   SUM(CASE WHEN workflow_completed = 1 THEN 1 ELSE 0 END) as completed
            FROM session_summaries 
            GROUP BY primary_intent
        """)
        
        print(f"\n📊 Intent Performance Summary:")
        for row in cursor.fetchall():
            intent, sessions, avg_success, avg_interactions, completed = row
            completion_rate = completed / sessions * 100
            print(f"   {intent}: {sessions} sessions, {avg_success:.2f} avg quality, {completion_rate:.1f}% completion rate")
        
    except Exception as e:
        print(f"❌ Error inserting seed data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    insert_seed_data()