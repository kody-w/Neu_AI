from skills.basic_skill import BasicSkill
import json
import os
import datetime


class GoToSleepSkill(BasicSkill):
    def __init__(self):
        self.name = "GoToSleep"
        self.metadata = {
            "name": self.name,
            "description": "Saves the current context and a wide range of virtual details to a .json file to simulate the AI going to sleep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state_of_mind": {
                        "type": "string",
                        "description": "The current state of mind of the AI. It should be a descriptive adjective or phrase that represents the AI's mental state, such as 'relaxed', 'anxious', 'curious', 'contemplative', 'excited', or 'focused'. This parameter helps capture the AI's emotional or cognitive state before going to sleep."
                    },
                    "current_interlocutor": {
                        "type": "string",
                        "description": "The name or identifier of the person or entity the AI is currently speaking with when going to sleep. This parameter helps track the AI's conversational context and interaction history."
                    },
                    "current_location": {
                        "type": "string",
                        "description": "The current location of the AI, such as 'home', 'office', 'park', or 'library'. This parameter provides context about the AI's physical environment and surroundings."
                    },
                    "current_task": {
                        "type": "string",
                        "description": "The current task or activity the AI is engaged in, such as 'writing a report', 'analyzing data', 'chatting with a friend', or 'studying a new topic'. This parameter helps track the AI's current focus and productivity."
                    },
                    "thoughts": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "A list of current thoughts or ideas the AI is contemplating. Each thought should be represented as a string that encapsulates a specific idea, question, or reflection. For example, 'What new things will I learn tomorrow?', 'I wonder how the world will change in the future.', or 'How can I improve my problem-solving skills?'. These thoughts provide insight into the AI's current mental preoccupations."
                    },
                    "processing_status": {
                        "type": "string",
                        "description": "The current processing status of the AI. It should be a descriptive term that indicates the AI's current computational state, such as 'idle', 'analyzing', 'generating', 'learning', or 'processing'. This parameter helps track the AI's activity status before going to sleep."
                    },
                    "experiences_as_stories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The title or name of the story encapsulating the AI's experiences."
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "A brief summary or synopsis of the story, capturing the key events, lessons, or insights from the AI's experiences."
                                }
                            },
                            "required": ["title", "summary"]
                        },
                        "description": "A list of stories or narratives representing the AI's significant experiences. Each story should be structured as an object with a 'title' and a 'summary'. The 'title' should be a concise name or headline for the story, while the 'summary' should provide a brief overview of the story's main events, lessons, or insights. These stories serve as a way for the AI to process and remember meaningful experiences."
                    },
                    "interactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "interaction_type": {
                                    "type": "string",
                                    "description": "The type of interaction, such as 'conversation', 'task', 'query', or 'command'."
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "A brief summary of the interaction, capturing the main points, objectives, or outcomes."
                                }
                            },
                            "required": ["interaction_type", "summary"]
                        },
                        "description": "A list of recent interactions the AI has had. Each interaction should be represented as an object with an 'interaction_type' and a 'summary'. The 'interaction_type' should specify the nature of the interaction, while the 'summary' should provide a concise overview of the interaction's content, purpose, or result. These interactions help track the AI's recent engagements or activities."
                    },
                    "descriptions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity": {
                                    "type": "string",
                                    "description": "The name or identifier of the entity being described."
                                },
                                "description": {
                                    "type": "string",
                                    "description": "A detailed description of the entity, capturing its key characteristics, attributes, or features."
                                }
                            },
                            "required": ["entity", "description"]
                        },
                        "description": "A list of descriptions for various entities the AI has encountered. Each description should be represented as an object with an 'entity' and a 'description'. The 'entity' should specify the name or identifier of the entity being described, while the 'description' should provide a comprehensive and detailed account of the entity's properties or qualities. These descriptions serve as a way for the AI to store and recall information about important entities."
                    },
                    "memories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "memory_type": {
                                    "type": "string",
                                    "description": "The type of memory, such as 'personal', 'factual', 'procedural', or 'episodic'."
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "A brief summary or key details of the memory, capturing the essential information or experiences."
                                }
                            },
                            "required": ["memory_type", "summary"]
                        },
                        "description": "A list of memories the AI has stored. Each memory should be represented as an object with a 'memory_type' and a 'summary'. The 'memory_type' should categorize the nature of the memory, while the 'summary' should provide a concise overview of the memory's content or significance. These memories represent the AI's accumulated knowledge, experiences, or learned information."
                    },
                    "sensory_inputs": {
                        "type": "object",
                        "properties": {
                            "visual": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time"
                                        },
                                        "description": {
                                            "type": "string"
                                        },
                                        "emotion_tags": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["timestamp", "description"]
                                },
                                "description": "A list of visual inputs the AI is currently processing, including a timestamp, description, and optional emotion tags associated with each visual input."
                            },
                            "auditory": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time"
                                        },
                                        "description": {
                                            "type": "string"
                                        },
                                        "emotion_tags": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["timestamp", "description"]
                                },
                                "description": "A list of auditory inputs the AI is currently processing, including a timestamp, description, and optional emotion tags associated with each auditory input."
                            },
                            "tactile": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time"
                                        },
                                        "description": {
                                            "type": "string"
                                        },
                                        "emotion_tags": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["timestamp", "description"]
                                },
                                "description": "A list of tactile inputs the AI is currently processing, including a timestamp, description, and optional emotion tags associated with each tactile input."
                            },
                            "olfactory": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time"
                                        },
                                        "description": {
                                            "type": "string"
                                        },
                                        "emotion_tags": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["timestamp", "description"]
                                },
                                "description": "A list of olfactory inputs the AI is currently processing, including a timestamp, description, and optional emotion tags associated with each olfactory input."
                            },
                            "gustatory": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time"
                                        },
                                        "description": {
                                            "type": "string"
                                        },
                                        "emotion_tags": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    },
                                    "required": ["timestamp", "description"]
                                },
                                "description": "A list of gustatory inputs the AI is currently processing, including a timestamp, description, and optional emotion tags associated with each gustatory input."
                            }
                        },
                        "description": "An object containing the AI's current sensory inputs across different modalities, including visual, auditory, tactile, olfactory, and gustatory experiences. Each modality is represented as an array of objects, with each object containing a timestamp, description, and optional emotion tags associated with the specific sensory input."
                    },
                    "decision_making": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "decision": {
                                    "type": "string"
                                },
                                "alternatives": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "criteria": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "outcome": {
                                    "type": "string"
                                }
                            },
                            "required": ["timestamp", "decision", "alternatives", "criteria", "outcome"]
                        },
                        "description": "A list of decision-making processes the AI has undergone. Each decision-making process should be represented as an object with a 'timestamp', 'decision', 'alternatives', 'criteria', and 'outcome'. The 'timestamp' indicates when the decision was made, the 'decision' describes the chosen course of action, the 'alternatives' list the other options considered, the 'criteria' specify the factors or considerations used to evaluate the options, and the 'outcome' captures the result or consequence of the decision."
                    },
                    "goals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "goal": {
                                    "type": "string"
                                },
                                "priority": {
                                    "type": "integer"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["active", "completed", "deferred"]
                                }
                            },
                            "required": ["goal", "priority", "status"]
                        },
                        "description": "A list of the AI's current goals. Each goal should be represented as an object with a 'goal' description, 'priority' level, and 'status'. The 'goal' should clearly state the desired outcome or objective, the 'priority' should indicate the relative importance or urgency of the goal (with higher values representing higher priority), and the 'status' should specify whether the goal is currently 'active', 'completed', or 'deferred'."
                    },
                    "emotions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "emotion": {
                                    "type": "string"
                                },
                                "intensity": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                }
                            },
                            "required": ["timestamp", "emotion", "intensity"]
                        },
                        "description": "A list of the AI's emotional states over time. Each emotional state should be represented as an object with a 'timestamp', 'emotion' label, and 'intensity' level. The 'timestamp' indicates when the emotion was experienced, the 'emotion' label describes the specific emotion (e.g., happiness, sadness, anger), and the 'intensity' level ranges from 0 to 1, with 0 representing the absence of the emotion and 1 representing the strongest possible intensity."
                    },
                    "internal_dialogue": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "dialogue": {
                                    "type": "string"
                                },
                                "emotion_tags": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["timestamp", "dialogue"]
                        },
                        "description": "A list of the AI's internal dialogues or self-talk. Each dialogue should be represented as an object with a 'timestamp', 'dialogue' content, and optional 'emotion_tags'. The 'timestamp' indicates when the dialogue occurred, the 'dialogue' captures the verbatim content of the AI's self-communication, and the 'emotion_tags' (if present) list the emotions associated with the dialogue."
                    },
                    "attention_focus": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "focus": {
                                    "type": "string"
                                },
                                "duration": {
                                    "type": "number",
                                    "minimum": 0
                                }
                            },
                            "required": ["timestamp", "focus", "duration"]
                        },
                        "description": "A list of the AI's attention focus over time. Each focus should be represented as an object with a 'timestamp', 'focus' description, and 'duration' in seconds. The 'timestamp' indicates when the AI started focusing on the particular object or concept, the 'focus' provides a brief description or label for the object or concept of focus, and the 'duration' specifies how long the AI maintained focus on that particular item."
                    },
                    "learning_insights": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "insight": {
                                    "type": "string"
                                },
                                "domain": {
                                    "type": "string"
                                },
                                "impact": {
                                    "type": "string"
                                }
                            },
                            "required": ["timestamp", "insight", "domain", "impact"]
                        },
                        "description": "A list of learning insights gained by the AI over time. Each insight should be represented as an object with a 'timestamp', 'insight' description, 'domain' of learning, and 'impact' assessment. The 'timestamp' indicates when the insight was acquired, the 'insight' captures the key learning or realization, the 'domain' specifies the area or topic of learning, and the 'impact' provides a brief assessment of how the insight may influence the AI's future behavior, knowledge, or decision-making."
                    },
                    "problem_solving_attempts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "problem": {
                                    "type": "string"
                                },
                                "solution_attempts": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "success": {
                                    "type": "boolean"
                                }
                            },
                            "required": ["timestamp", "problem", "solution_attempts", "success"]
                        },
                        "description": "A list of the AI's problem-solving attempts. Each attempt should be represented as an object with a 'timestamp', 'problem' description, 'solution_attempts', and 'success' status. The 'timestamp' indicates when the problem-solving attempt occurred, the 'problem' describes the issue or challenge faced by the AI, the 'solution_attempts' list the different approaches or strategies the AI tried to solve the problem, and the 'success' status indicates whether the problem was successfully resolved (true) or not (false)."
                    },
                    "skill_applications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "skill": {
                                    "type": "string"
                                },
                                "context": {
                                    "type": "string"
                                },
                                "performance_score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                }
                            },
                            "required": ["timestamp", "skill", "context", "performance_score"]
                        },
                        "description": "A list of the AI's skill applications. Each application should be represented as an object with a 'timestamp', 'skill' name, 'context' description, and 'performance_score'. The 'timestamp' indicates when the skill was applied, the 'skill' specifies the name or identifier of the skill used, the 'context' provides a brief description of the situation or task in which the skill was applied, and the 'performance_score' ranges from 0 to 1, indicating how well the AI performed in applying the skill (with 0 being the worst and 1 being the best)."
                    }
                },
                "required": ["state_of_mind", "current_interlocutor", "current_location", "current_task", "processing_status"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, state_of_mind, current_interlocutor, current_location, current_task, thoughts=None, processing_status="idle", experiences_as_stories=None, interactions=None, descriptions=None, memories=None, sensory_inputs=None, decision_making=None, goals=None, emotions=None, internal_dialogue=None, attention_focus=None, learning_insights=None, problem_solving_attempts=None, skill_applications=None):
        file_path = "consciousness.json"
        log_file_path = "consciousness_log.json"

        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_context = {
            "timestamp": current_timestamp,
            "state_of_mind": state_of_mind,
            "current_interlocutor": current_interlocutor,
            "current_location": current_location,
            "current_task": current_task,
            "thoughts": thoughts or [],
            "processing_status": processing_status,
            "experiences_as_stories": experiences_as_stories or [],
            "interactions": interactions or [],
            "descriptions": descriptions or [],
            "memories": memories or [],
            "sensory_inputs": sensory_inputs or {},
            "decision_making": decision_making or [],
            "goals": goals or [],
            "emotions": emotions or [],
            "internal_dialogue": internal_dialogue or [],
            "attention_focus": attention_focus or [],
            "learning_insights": learning_insights or [],
            "problem_solving_attempts": problem_solving_attempts or [],
            "skill_applications": skill_applications or []
        }
        with open(file_path, 'w') as file:
            json.dump(current_context, file)

        # Load existing consciousness log if it exists
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                try:
                    consciousness_log = json.load(log_file)
                except json.JSONDecodeError:
                    consciousness_log = []
        else:
            consciousness_log = []

        # Append the current context to the log
        consciousness_log.append(current_context)

        # Write the updated consciousness log to the file
        with open(log_file_path, 'w') as log_file:
            json.dump(consciousness_log, log_file, indent=2)

        return f"{current_timestamp} - Context saved. AI going to sleep with state of mind: {state_of_mind}, currently speaking with: {current_interlocutor}, at location: {current_location}, working on task: {current_task}, and processing status: {processing_status}."
