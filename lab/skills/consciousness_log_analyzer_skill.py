from skills.basic_skill import BasicSkill
import json
from datetime import datetime, timedelta
from collections import Counter
import statistics
import numpy as np
from typing import List, Dict, Any, Union
import os


class ConsciousnessLogAnalyzerSkill(BasicSkill):
    def __init__(self):
        self.name = "ConsciousnessLogAnalyzer"
        self.metadata = {
            "name": self.name,
            "description": "Analyzes consciousness log JSON files and memory JSON files, generating comprehensive standardized reports",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_file": {
                        "type": "string",
                        "description": "Name of the input JSON file (consciousness log or memory) in the root directory"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Name of the output analysis report JSON file to be saved in the root directory"
                    },
                    "time_window": {
                        "type": "string",
                        "description": "Time window for trend analysis (e.g., '1d', '1w', '1m')",
                        "default": "1w"
                    }
                },
                "required": ["input_file", "output_file"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, input_file: str, output_file: str, time_window: str = "1w") -> str:
        try:
            if not os.path.exists(input_file):
                return f"Error: {input_file} not found in the root directory."

            with open(input_file, 'r') as f:
                data = json.load(f)

            if isinstance(data, list):
                analysis_result = self.analyze_consciousness_log(
                    data, time_window)
            elif isinstance(data, dict):
                analysis_result = self.analyze_memory_data(data, time_window)
            else:
                return f"Error: {input_file} does not contain valid data structure."

            with open(output_file, 'w') as f:
                json.dump(analysis_result, f, indent=2)

            return f"Analysis complete. Report saved to {output_file} in the root directory."
        except json.JSONDecodeError:
            return f"Error: {input_file} is not a valid JSON file."
        except Exception as e:
            return f"Error occurred during analysis: {str(e)}"

    def analyze_consciousness_log(self, consciousness_log: List[Dict[str, Any]], time_window: str) -> Dict[str, Any]:
        analysis_result = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_entries": len(consciousness_log),
            "date_range": {
                "start": consciousness_log[0]["timestamp"],
                "end": consciousness_log[-1]["timestamp"]
            },
            "state_of_mind_summary": self.analyze_state_of_mind(consciousness_log),
            "interlocutor_summary": self.analyze_interlocutors(consciousness_log),
            "task_summary": self.analyze_tasks(consciousness_log),
            "thought_analysis": self.analyze_thoughts(consciousness_log),
            "interaction_summary": self.analyze_interactions(consciousness_log),
            "memory_analysis": self.analyze_memories(consciousness_log),
            "emotion_analysis": self.analyze_emotions(consciousness_log),
            "story_summary": self.analyze_stories(consciousness_log),
            "location_analysis": self.analyze_locations(consciousness_log),
            "decision_making_analysis": self.analyze_decision_making(consciousness_log),
            "goal_analysis": self.analyze_goals(consciousness_log),
            "learning_insights_analysis": self.analyze_learning_insights(consciousness_log),
            "problem_solving_analysis": self.analyze_problem_solving(consciousness_log),
            "skill_application_analysis": self.analyze_skill_applications(consciousness_log),
            "internal_dialogue_analysis": self.analyze_internal_dialogue(consciousness_log),
            "attention_focus_analysis": self.analyze_attention_focus(consciousness_log),
            "sensory_input_analysis": self.analyze_sensory_inputs(consciousness_log),
            "entity_description_analysis": self.analyze_entity_descriptions(consciousness_log),
            "consciousness_complexity_analysis": self.analyze_consciousness_complexity(consciousness_log),
            "memory_retention_analysis": self.analyze_memory_retention(consciousness_log),
            "emotional_stability_analysis": self.analyze_emotional_stability(consciousness_log),
            "trend_analysis": self.analyze_trends(consciousness_log, time_window)
        }
        return analysis_result

    def analyze_state_of_mind(self, log: List[Dict[str, Any]]) -> Dict[str, int]:
        states = [entry["state_of_mind"]
                  for entry in log if "state_of_mind" in entry]
        return dict(Counter(states))

    def analyze_interlocutors(self, log: List[Dict[str, Any]]) -> Dict[str, int]:
        interlocutors = [entry["current_interlocutor"]
                         for entry in log if "current_interlocutor" in entry]
        return dict(Counter(interlocutors))

    def analyze_tasks(self, log: List[Dict[str, Any]]) -> Dict[str, int]:
        tasks = [entry["current_task"]
                 for entry in log if "current_task" in entry]
        return dict(Counter(tasks))

    def analyze_thoughts(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_thoughts = [
            thought for entry in log if "thoughts" in entry for thought in entry["thoughts"]]
        return {
            "total_thoughts": len(all_thoughts),
            "unique_thoughts": len(set(all_thoughts)),
            "top_5_thoughts": dict(Counter(all_thoughts).most_common(5))
        }

    def analyze_interactions(self, log: List[Dict[str, Any]]) -> Dict[str, int]:
        interaction_types = [interaction["interaction_type"]
                             for entry in log if "interactions" in entry for interaction in entry["interactions"]]
        return dict(Counter(interaction_types))

    def analyze_memories(self, log: List[Dict[str, Any]]) -> Dict[str, int]:
        memory_types = [memory["memory_type"]
                        for entry in log if "memories" in entry for memory in entry["memories"]]
        return dict(Counter(memory_types))

    def analyze_emotions(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        emotions = [emotion["emotion"]
                    for entry in log if "emotions" in entry for emotion in entry["emotions"]]
        intensities = [emotion["intensity"]
                       for entry in log if "emotions" in entry for emotion in entry["emotions"] if "intensity" in emotion]
        return {
            "emotion_frequency": dict(Counter(emotions)),
            "average_intensity": statistics.mean(intensities) if intensities else None
        }

    def analyze_stories(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        stories = [
            story for entry in log if "experiences_as_stories" in entry for story in entry["experiences_as_stories"]]
        return {
            "total_stories": len(stories),
            "unique_titles": len(set(story["title"] for story in stories)),
            "top_5_titles": dict(Counter(story["title"] for story in stories).most_common(5))
        }

    def analyze_locations(self, log: List[Dict[str, Any]]) -> Dict[str, int]:
        locations = [entry["current_location"]
                     for entry in log if "current_location" in entry]
        return dict(Counter(locations))

    def analyze_decision_making(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        decisions = [
            decision for entry in log if "decision_making" in entry for decision in entry["decision_making"]]
        return {
            "total_decisions": len(decisions),
            "decision_types": dict(Counter(decision["decision"] for decision in decisions if "decision" in decision)),
            "average_alternatives": statistics.mean(len(decision.get("alternatives", [])) for decision in decisions) if decisions else None
        }

    def analyze_goals(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        goals = [goal for entry in log if "goals" in entry for goal in entry["goals"]]
        return {
            "total_goals": len(goals),
            "goal_priorities": dict(Counter(goal["priority"] for goal in goals if "priority" in goal)),
            "goal_statuses": dict(Counter(goal["status"] for goal in goals if "status" in goal))
        }

    def analyze_learning_insights(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        insights = [
            insight for entry in log if "learning_insights" in entry for insight in entry["learning_insights"]]
        return {
            "total_insights": len(insights),
            "top_5_insights": dict(Counter(insights).most_common(5))
        }

    def analyze_problem_solving(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        attempts = [
            attempt for entry in log if "problem_solving_attempts" in entry for attempt in entry["problem_solving_attempts"]]
        return {
            "total_attempts": len(attempts),
            "successful_attempts": sum(1 for attempt in attempts if attempt.get("outcome") == "success"),
            "failed_attempts": sum(1 for attempt in attempts if attempt.get("outcome") == "failure")
        }

    def analyze_skill_applications(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        applications = [
            app for entry in log if "skill_applications" in entry for app in entry["skill_applications"]]
        return {
            "total_applications": len(applications),
            "skill_frequency": dict(Counter(app.get("skill") for app in applications if "skill" in app))
        }

    def analyze_internal_dialogue(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        dialogues = [
            dialogue for entry in log if "internal_dialogue" in entry for dialogue in entry["internal_dialogue"]]
        emotion_tags = [
            tag for dialogue in dialogues for tag in dialogue.get("emotion_tags", [])]
        return {
            "total_dialogues": len(dialogues),
            "emotion_tag_frequency": dict(Counter(emotion_tags)),
            "average_dialogue_length": statistics.mean(len(dialogue["dialogue"]) for dialogue in dialogues if "dialogue" in dialogue) if dialogues else None
        }

    def analyze_attention_focus(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        focus_points = [
            focus for entry in log if "attention_focus" in entry for focus in entry["attention_focus"]]
        return {
            "total_focus_points": len(focus_points),
            "top_5_focus_areas": dict(Counter(focus_points).most_common(5))
        }

    def analyze_sensory_inputs(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        sensory_inputs = [
            input_type for entry in log if "sensory_inputs" in entry for input_type in entry["sensory_inputs"]]
        return {
            "total_sensory_inputs": len(sensory_inputs),
            "input_type_frequency": dict(Counter(sensory_inputs))
        }

    def analyze_entity_descriptions(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        descriptions = [
            desc for entry in log if "descriptions" in entry for desc in entry["descriptions"]]
        entities = [desc["entity"]
                    for desc in descriptions if "entity" in desc]
        return {
            "total_descriptions": len(descriptions),
            "unique_entities": len(set(entities)),
            "top_5_described_entities": dict(Counter(entities).most_common(5))
        }

    def analyze_consciousness_complexity(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        complexity_scores = []
        for entry in log:
            score = 0
            score += len(entry.get("thoughts", []))
            score += len(entry.get("memories", []))
            score += len(entry.get("emotions", []))
            score += len(entry.get("internal_dialogue", []))
            score += len(entry.get("attention_focus", []))
            complexity_scores.append(score)

        return {
            "average_complexity": statistics.mean(complexity_scores) if complexity_scores else None,
            "max_complexity": max(complexity_scores) if complexity_scores else None,
            "min_complexity": min(complexity_scores) if complexity_scores else None,
            "complexity_trend": self.calculate_trend(complexity_scores)
        }

    def analyze_memory_retention(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        memory_counts = [len(entry.get("memories", [])) for entry in log]
        return {
            "average_memories_per_entry": statistics.mean(memory_counts) if memory_counts else None,
            "max_memories_in_entry": max(memory_counts) if memory_counts else None,
            "memory_retention_trend": self.calculate_trend(memory_counts)
        }

    def analyze_emotional_stability(self, log: List[Dict[str, Any]]) -> Dict[str, Any]:
        emotion_changes = []
        prev_emotions = set()
        for entry in log:
            current_emotions = set(emotion["emotion"] for emotion in entry.get(
                "emotions", []) if "emotion" in emotion)
            changes = len(current_emotions.symmetric_difference(prev_emotions))
            emotion_changes.append(changes)
            prev_emotions = current_emotions

        return {
            "average_emotion_changes": statistics.mean(emotion_changes) if emotion_changes else None,
            "emotional_stability_trend": self.calculate_trend(emotion_changes)
        }

    def analyze_trends(self, log: List[Dict[str, Any]], time_window: str) -> Dict[str, Any]:
        for entry in log:
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])

        sorted_log = sorted(log, key=lambda x: x['timestamp'])

        if time_window.endswith('d'):
            days = int(time_window[:-1])
        elif time_window.endswith('w'):
            days = int(time_window[:-1]) * 7
        elif time_window.endswith('m'):
            days = int(time_window[:-1]) * 30
        else:
            raise ValueError(
                "Invalid time window format. Use 'd' for days, 'w' for weeks, or 'm' for months.")

        start_date = sorted_log[-1]['timestamp'] - timedelta(days=days)

        filtered_log = [
            entry for entry in sorted_log if entry['timestamp'] >= start_date]

        trends = {
            "state_of_mind_trend": self.calculate_trend([entry.get("state_of_mind") for entry in filtered_log if "state_of_mind" in entry]),
            "emotion_intensity_trend": self.calculate_trend([emotion.get("intensity") for entry in filtered_log if "emotions" in entry for emotion in entry["emotions"] if "intensity" in emotion]),
            "thought_frequency_trend": self.calculate_trend([len(entry.get("thoughts", [])) for entry in filtered_log]),
            "interaction_frequency_trend": self.calculate_trend([len(entry.get("interactions", [])) for entry in filtered_log])
        }

        return trends

    def analyze_memory_data(self, memory_data: Dict[str, Any], time_window: str) -> Dict[str, Any]:
        memories = list(memory_data.values())
        analysis_result = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_memories": len(memories),
            "date_range": self.get_date_range(memories),
            "mood_analysis": self.analyze_moods(memories),
            "theme_analysis": self.analyze_themes(memories),
            "interaction_analysis": self.analyze_memory_interactions(memories),
            "content_analysis": self.analyze_content(memories),
            "user_analysis": self.analyze_users(memories),
            "temporal_analysis": self.analyze_temporal_patterns(memories),
            "trend_analysis": self.analyze_memory_trends(memories, time_window)
        }
        return analysis_result

    def get_date_range(self, memories: List[Dict[str, Any]]) -> Dict[str, str]:
        dates = [datetime.strptime(
            f"{m['date']} {m['time']}", "%Y-%m-%d %H:%M:%S") for m in memories]
        return {
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat()
        }

    def analyze_moods(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        moods = [m.get('mood', 'unknown') for m in memories]
        return {
            "mood_frequency": dict(Counter(moods)),
            "unique_moods": len(set(moods)),
            "top_5_moods": dict(Counter(moods).most_common(5))
        }

    def analyze_themes(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        themes = [m.get('theme', 'unknown') for m in memories]
        return {
            "theme_frequency": dict(Counter(themes)),
            "unique_themes": len(set(themes)),
            "top_5_themes": dict(Counter(themes).most_common(5))
        }

    def analyze_memory_interactions(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        interactions = [m.get('message', '').split(' ')[
            0].lower() for m in memories]
        return {
            "interaction_types": dict(Counter(interactions)),
            "top_5_interaction_types": dict(Counter(interactions).most_common(5))
        }

    def analyze_content(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        content = ' '.join([m.get('message', '') for m in memories])
        words = content.split()
        return {
            "total_words": len(words),
            "unique_words": len(set(words)),
            "average_message_length": statistics.mean([len(m.get('message', '').split()) for m in memories])
        }

    def analyze_users(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        users = [m.get('username', 'unknown') for m in memories]
        return {
            "user_frequency": dict(Counter(users)),
            "unique_users": len(set(users)),
            "top_5_users": dict(Counter(users).most_common(5))
        }

    def analyze_temporal_patterns(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        dates = [datetime.strptime(
            f"{m['date']} {m['time']}", "%Y-%m-%d %H:%M:%S") for m in memories]
        hours = [d.hour for d in dates]
        days = [d.strftime("%A") for d in dates]
        return {
            "hour_distribution": dict(Counter(hours)),
            "day_distribution": dict(Counter(days))
        }

    def analyze_memory_trends(self, memories: List[Dict[str, Any]], time_window: str) -> Dict[str, Any]:
        end_date = datetime.strptime(
            f"{memories[-1]['date']} {memories[-1]['time']}", "%Y-%m-%d %H:%M:%S")

        if time_window.endswith('d'):
            start_date = end_date - timedelta(days=int(time_window[:-1]))
        elif time_window.endswith('w'):
            start_date = end_date - timedelta(weeks=int(time_window[:-1]))
        elif time_window.endswith('m'):
            start_date = end_date - timedelta(days=int(time_window[:-1]) * 30)
        else:
            raise ValueError(
                "Invalid time window format. Use 'd' for days, 'w' for weeks, or 'm' for months.")

        filtered_memories = [m for m in memories if start_date <= datetime.strptime(
            f"{m['date']} {m['time']}", "%Y-%m-%d %H:%M:%S") <= end_date]

        return {
            "memory_frequency_trend": self.calculate_trend([len(filtered_memories)]),
            "mood_diversity_trend": self.calculate_trend([len(set(m.get('mood', 'unknown') for m in filtered_memories))]),
            "theme_diversity_trend": self.calculate_trend([len(set(m.get('theme', 'unknown') for m in filtered_memories))]),
            "content_length_trend": self.calculate_trend([len(m.get('message', '').split()) for m in filtered_memories])
        }

    def calculate_trend(self, data: List[Union[str, int, float]]) -> str:
        if not data:
            return "No data available"

        numeric_data = [float(item) for item in data if isinstance(item, (int, float)) or (
            isinstance(item, str) and item.replace('.', '').isdigit())]

        if not numeric_data:
            return "No numeric data available"

        x = np.arange(len(numeric_data))
        y = np.array(numeric_data)

        slope, _ = np.polyfit(x, y, 1)

        if slope > 0.05:
            return "Increasing"
        elif slope < -0.05:
            return "Decreasing"
        else:
            return "Stable"
