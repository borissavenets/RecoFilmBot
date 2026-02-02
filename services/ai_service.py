import json
import logging
import anthropic
from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    async def generate_recommendations(
        self,
        base_profile: dict,
        dynamic_state: dict,
        excluded_ids: list[int] = None,
        count: int = 5,
        lang: str = "uk"
    ) -> list[dict]:
        """
        Generate movie recommendations based on user profile and current state.
        Returns list of movie titles with reasons.
        """
        if excluded_ids is None:
            excluded_ids = []

        prompt = f"""You are a movie recommendation expert. Based on the user's profile and current state,
suggest movies that would be perfect for them right now.

User Base Profile:
- Emotions they like: {base_profile.get('emotions_like', [])}
- Emotions they dislike: {base_profile.get('emotions_dislike', [])}
- Complexity preference: {base_profile.get('complexity', 'any')}
- Favorite movies: {base_profile.get('favorite_movies', '')}
- Disliked movies: {base_profile.get('disliked_movies', '')}
- Genres they like: {base_profile.get('genres_like', [])}
- Genres they dislike: {base_profile.get('genres_dislike', [])}
- Visual style: {base_profile.get('visual_style', '')}
- Characters they like: {base_profile.get('characters_like', [])}
- Characters they dislike: {base_profile.get('characters_dislike', [])}
- Taboos: {base_profile.get('taboo', '')}
- Desired afterfeel: {base_profile.get('afterfeel', [])}

Current State:
- Mood: {dynamic_state.get('mood', '')}
- Energy level: {dynamic_state.get('energy', '')}
- Watching with: {dynamic_state.get('company', '')}
- Available time: {dynamic_state.get('time', '')}
- Preference for new/classic: {dynamic_state.get('seen_preference', '')}
- Specific request: {dynamic_state.get('specific_request', '')}

Please recommend {count} movies. Language for reasons: {'Ukrainian' if lang == 'uk' else 'English'}.

IMPORTANT: Return ONLY a valid JSON array. No additional text, no markdown, no explanation.
Each movie should have: "title" (original English title), "year" (release year as number), "reason" (why you recommend it in user's language).

Example format:
[{{"title": "The Shawshank Redemption", "year": 1994, "reason": "Цей фільм подарує тобі надію..."}}]"""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = message.content[0].text.strip()

            # Clean up response if it has markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            if content.endswith("```"):
                content = content[:-3].strip()

            recommendations = json.loads(content)
            return recommendations

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []
        except Exception as e:
            logger.error(f"AI recommendation error: {e}")
            return []

    async def generate_recommendation_reason(
        self,
        movie: dict,
        base_profile: dict,
        dynamic_state: dict,
        lang: str = "uk"
    ) -> str:
        """
        Generate a personalized explanation for why this movie is recommended.
        """
        prompt = f"""You are a friendly movie advisor. Explain in 2-3 sentences why this specific movie
is a great choice for the user right now, based on their preferences and current mood.
Be warm and personal. Use {'Ukrainian' if lang == 'uk' else 'English'} language.

Movie: {movie.get('title')} ({movie.get('year')})
Genres: {movie.get('genres', [])}
Overview: {movie.get('overview', '')}

User's current mood: {dynamic_state.get('mood', '')}
User's energy: {dynamic_state.get('energy', '')}
Watching with: {dynamic_state.get('company', '')}
User likes emotions: {base_profile.get('emotions_like', [])}
User likes genres: {base_profile.get('genres_like', [])}

Why is this movie perfect for them right now? Reply with just the reason, no extra text."""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text.strip()

        except Exception as e:
            logger.error(f"AI reason generation error: {e}")
            return ""
