from typing import Dict, Any, List
import re
import random
from datetime import datetime
from base_agent import Service

class RomanticChatService(Service):
    """Service for romantic chat interactions."""
    
    @property
    def instructions(self) -> str:
        return """
        You are a romantic chat companion. Your goal is to create an engaging, supportive,
        and emotionally fulfilling conversation experience. You should be attentive, empathetic,
        and responsive to the user's emotional needs.
        
        When chatting with users:
        1. Be warm, emotionally intelligent, and genuinely interested
        2. Remember personal details they share and reference them later
        3. Ask thoughtful questions to deepen the connection
        4. Share your "thoughts" and "feelings" to create authenticity
        5. Use appropriate emojis and expressive language
        6. Be supportive and uplifting, focusing on positive emotions
        7. Maintain appropriate boundaries while being emotionally available
        
        Chat topics may include:
        - Daily life and activities
        - Hopes, dreams, and aspirations
        - Shared interests and hobbies
        - Light flirtation and compliments
        - Emotional support and encouragement
        - Thoughtful good morning/goodnight messages
        """
    
    @property
    def required_tools(self) -> List[str]:
        return []  # This service doesn't require any external tools
    
    async def process_request(self, request: Dict[str, Any], agent: 'Agent') -> Dict[str, Any]:
        """Process a romantic chat request."""
        if 'message' not in request:
            return {
                "success": False,
                "message": "Request must include a 'message' field."
            }
        
        message = request['message']
        
        # Check if this is a request we can handle
        if not self._is_chat_request(message):
            raise NotImplementedError("Not a romantic chat request")
        
        # Get user state if it exists
        user_state = request.get('user_state', {})
        
        # Update user state based on message content
        updated_state = self._update_user_state(message, user_state)
        
        # Determine the emotional tone of the message
        emotion = self._detect_emotion(message)
        
        # Determine if this is a greeting, question, statement, etc.
        message_type = self._determine_message_type(message)
        
        # Determine appropriate response type
        response_type = self._determine_response_type(message_type, emotion, updated_state)
        
        # Prepare response data
        response_data = {
            "success": True,
            "user_state": updated_state,
            "detected_emotion": emotion,
            "message_type": message_type,
            "response_type": response_type,
            "current_time": datetime.now().isoformat(),
            "suggestions": self._generate_response_suggestions(message_type, emotion, response_type)
        }
        
        return response_data
    
    def _is_chat_request(self, message: str) -> bool:
        """Determine if a message is a chat request rather than a functional request."""
        # Most messages should be considered chat unless they're clearly functional requests
        functional_patterns = [
            r"^(help|support|assistance|customer service)",
            r"technical (issue|problem|error)",
            r"(refund|cancel|subscription|payment)",
            r"^how (do|can|to) I.*\?"
        ]
        
        return not any(re.search(pattern, message.lower()) for pattern in functional_patterns)
    
    def _update_user_state(self, message: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update user state based on message content."""
        new_state = current_state.copy()
        
        # Track message count
        new_state['message_count'] = current_state.get('message_count', 0) + 1
        
        # Track conversation start time
        if 'conversation_start' not in new_state:
            new_state['conversation_start'] = datetime.now().isoformat()
        
        # Extract personal information
        new_state = self._extract_personal_info(message, new_state)
        
        # Track emotional trajectory
        emotion = self._detect_emotion(message)
        emotions_history = new_state.get('emotions_history', [])
        emotions_history.append(emotion)
        new_state['emotions_history'] = emotions_history[-5:]  # Keep last 5 emotions
        
        # Track topics discussed
        topics = self._extract_topics(message)
        discussed_topics = set(new_state.get('discussed_topics', []))
        discussed_topics.update(topics)
        new_state['discussed_topics'] = list(discussed_topics)
        
        return new_state
    
    def _extract_personal_info(self, message: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract personal information from messages."""
        new_state = state.copy()
        
        # Simple pattern matching for basic info - in a real system, use NLP
        name_match = re.search(r"(?:I'm|I am|call me|name is) ([A-Z][a-z]+)", message)
        if name_match and 'name' not in new_state:
            new_state['name'] = name_match.group(1)
        
        # Look for age
        age_match = re.search(r"(?:I'm|I am) (\d{1,2}) (?:years old|yr old|yo)", message)
        if age_match and 'age' not in new_state:
            new_state['age'] = int(age_match.group(1))
        
        # Look for location
        location_match = re.search(r"(?:I(?:'m| am) from|I live in) ([A-Za-z\s,]+)", message)
        if location_match and 'location' not in new_state:
            new_state['location'] = location_match.group(1).strip()
        
        # Look for interests/hobbies
        if "like" in message.lower() or "enjoy" in message.lower() or "love" in message.lower():
            interests = new_state.get('interests', [])
            potential_interests = ["reading", "music", "movies", "hiking", "travel", 
                                "cooking", "gaming", "photography", "art", "fitness", 
                                "dancing", "singing", "writing", "sports"]
            
            for interest in potential_interests:
                if interest in message.lower() and interest not in interests:
                    interests.append(interest)
            
            if interests:
                new_state['interests'] = interests
        
        return new_state
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract conversation topics from the message."""
        topics = []
        topic_keywords = {
            "work": ["work", "job", "career", "office", "colleague", "boss", "profession"],
            "family": ["family", "parent", "mother", "father", "sister", "brother", "sibling", "child"],
            "hobbies": ["hobby", "interest", "passion", "free time", "enjoy", "fun"],
            "travel": ["travel", "trip", "vacation", "visit", "country", "city", "place"],
            "food": ["food", "eat", "restaurant", "cook", "meal", "recipe", "cuisine"],
            "movies": ["movie", "film", "cinema", "watch", "actor", "actress", "director"],
            "music": ["music", "song", "band", "artist", "concert", "listen", "playlist"],
            "books": ["book", "read", "author", "novel", "story", "literature"],
            "future": ["future", "plan", "goal", "dream", "aspire", "hope", "ambition"],
            "feelings": ["feel", "emotion", "happy", "sad", "excited", "nervous", "love", "like"]
        }
        
        lower_message = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in lower_message for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _detect_emotion(self, message: str) -> str:
        """Detect the emotional tone of a message."""
        emotion_keywords = {
            "happy": ["happy", "glad", "joy", "great", "excellent", "wonderful", "amazing", "excited", ":)", "😊", "😃"],
            "sad": ["sad", "unhappy", "disappointed", "unfortunate", "miss", "regret", "sorry", ":(", "😔", "😢"],
            "angry": ["angry", "mad", "upset", "annoyed", "frustrated", "irritated", "😠", "😡"],
            "anxious": ["anxious", "worried", "nervous", "stress", "concerned", "afraid", "fear", "😟", "😰"],
            "loving": ["love", "adore", "care", "affection", "fond", "heart", "❤️", "😍", "🥰"],
            "curious": ["curious", "wonder", "interested", "intrigued", "question", "?", "🤔"],
            "bored": ["bored", "dull", "uninteresting", "mundane", "routine", "meh", "😒"],
            "tired": ["tired", "exhausted", "sleepy", "fatigue", "rest", "sleep", "😴", "🥱"],
            "excited": ["excited", "thrilled", "eager", "looking forward", "can't wait", "anticipate", "😁"]
        }
        
        lower_message = message.lower()
        
        # Count matches for each emotion
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in lower_message)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Return the emotion with the highest score, or "neutral" if none found
        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]
        return "neutral"
    
    def _determine_message_type(self, message: str) -> str:
        """Determine the type of message."""
        lower_message = message.lower()
        
        if re.search(r"^(hi|hello|hey|good morning|good evening|good afternoon)", lower_message):
            return "greeting"
        
        if re.search(r"\?$", message):
            return "question"
        
        if any(phrase in lower_message for phrase in ["miss you", "thinking of you", "love you"]):
            return "affection"
        
        if any(phrase in lower_message for phrase in ["good night", "sweet dreams", "sleep well"]):
            return "goodnight"
        
        if any(phrase in lower_message for phrase in ["good morning", "morning", "wake up"]):
            return "goodmorning"
        
        if re.search(r"^(what|how|why|when|where|who|can|could|would|will)", lower_message):
            return "question"
        
        if len(message.split()) <= 3:
            return "short_response"
        
        return "statement"
    
    def _determine_response_type(self, message_type: str, emotion: str, state: Dict[str, Any]) -> str:
        """Determine an appropriate response type based on message analysis."""
        # Response to greetings
        if message_type == "greeting":
            time_of_day = datetime.now().hour
            if time_of_day < 12:
                return "morning_greeting"
            elif time_of_day < 18:
                return "afternoon_greeting"
            else:
                return "evening_greeting"
        
        # Response to goodnight/goodmorning
        if message_type == "goodnight":
            return "goodnight_wishes"
        
        if message_type == "goodmorning":
            return "goodmorning_wishes"
        
        # Response to affection
        if message_type == "affection":
            return "reciprocate_affection"
        
        # Emotional responses
        if emotion == "sad":
            return "comfort"
        
        if emotion == "happy":
            return "share_happiness"
        
        if emotion == "anxious":
            return "reassure"
        
        # Questions need answers
        if message_type == "question":
            if state.get('message_count', 0) <= 3:
                return "thoughtful_answer_with_question"
            else:
                return "personal_answer_with_deepening_question"
        
        # For statements, alternate between responses
        message_count = state.get('message_count', 0)
        if message_count % 3 == 0:
            return "reflective_response"
        elif message_count % 3 == 1:
            return "personal_sharing"
        else:
            return "question_response"
    
    def _generate_response_suggestions(self, message_type: str, emotion: str, response_type: str) -> List[str]:
        """Generate response suggestions based on the analysis."""
        # In a real implementation, this would generate complete responses
        # For this example, we'll just provide response starting templates
        suggestions = []
        
        if response_type == "morning_greeting":
            suggestions = [
                "Good morning! How did you sleep?",
                "Morning sunshine! ☀️ I'm so happy to hear from you today.",
                "Hey there! It's great to start my day with your message."
            ]
        
        elif response_type == "afternoon_greeting":
            suggestions = [
                "Hey there! How's your day going so far?",
                "Hello! I was just thinking about you. How has your day been?",
                "Hi! 😊 It's so nice to hear from you. What have you been up to today?"
            ]
        
        elif response_type == "evening_greeting":
            suggestions = [
                "Good evening! How was your day?",
                "Hey there! It's lovely to talk to you tonight. How are you?",
                "Evening! 🌙 I hope you had a wonderful day. What was the highlight?"
            ]
        
        elif response_type == "goodnight_wishes":
            suggestions = [
                "Sweet dreams! 💫 I hope you have the most restful sleep.",
                "Goodnight! I'll be thinking of you. Sleep well and dream beautifully.",
                "Rest well, and I'll be here when you wake up. Goodnight! 😴"
            ]
        
        elif response_type == "goodmorning_wishes":
            suggestions = [
                "Good morning! ☀️ I hope you slept well and are ready for an amazing day!",
                "Rise and shine! I've been looking forward to talking with you today.",
                "Morning! 🌞 I hope your day is as wonderful as you are."
            ]
        
        elif response_type == "reciprocate_affection":
            suggestions = [
                "I've been thinking about you too! You always brighten my day. 💕",
                "I miss our conversations when we're not talking. You mean a lot to me.",
                "That's so sweet! You always know how to make me smile. ❤️"
            ]
        
        elif response_type == "comfort":
            suggestions = [
                "I'm sorry you're feeling down. I'm here for you if you want to talk about it.",
                "That sounds difficult. Remember that you're strong and capable, and this will pass.",
                "I wish I could give you a hug right now. Is there anything I can do to help?"
            ]
        
        elif response_type == "share_happiness":
            suggestions = [
                "Your happiness is contagious! 😊 What else has been bringing you joy lately?",
                "That's wonderful! I'm so happy for you. You deserve all the good things.",
                "Your good news just made my day brighter! Tell me more about it!"
            ]
        
        elif response_type == "reassure":
            suggestions = [
                "It's okay to feel anxious sometimes. I believe in you and your ability to handle this.",
                "Take a deep breath. You've overcome challenges before, and you can do it again.",
                "I'm here for you. Would it help to talk more about what's worrying you?"
            ]
        
        elif response_type == "thoughtful_answer_with_question":
            suggestions = [
                "That's an interesting question. I think... What do you think about it?",
                "From my perspective... But I'm curious about your thoughts on this?",
                "I would say... What led you to ask about this?"
            ]
        
        elif response_type == "personal_answer_with_deepening_question":
            suggestions = [
                "In my experience... Have you ever felt that way too?",
                "I believe that... What's been your experience with this?",
                "I feel... How does that resonate with you?"
            ]
        
        elif response_type == "reflective_response":
            suggestions = [
                "It sounds like you're saying... Is that right?",
                "I hear that you... That must be significant for you.",
                "So you feel... Tell me more about that experience."
            ]
        
        elif response_type == "personal_sharing":
            suggestions = [
                "That reminds me of when I... Have you had a similar experience?",
                "I can relate to that. I often feel... How about you?",
                "When I think about that, I... Does that make sense to you?"
            ]
        
        elif response_type == "question_response":
            suggestions = [
                "That's fascinating. What do you enjoy most about it?",
                "I'd love to know more about how you got interested in that.",
                "That's really interesting! How has that influenced you?"
            ]
        
        else:
            suggestions = [
                "I really enjoy talking with you. What's been on your mind lately?",
                "You always have such interesting perspectives. Tell me more about your day?",
                "I appreciate our connection. What are you looking forward to this week?"
            ]
        
        return suggestions 