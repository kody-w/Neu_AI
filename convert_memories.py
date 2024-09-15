import json
from datetime import datetime

def summarize_memories(file_path):
    with open(file_path, 'r') as f:
        memories = json.load(f)
    
    core_memories = memories['core_memories']
    associated_memories = memories['associated_memories']
    
    print(f"Total core memories: {len(core_memories)}")
    print(f"Total associated memories: {len(associated_memories)}")
    
    if core_memories:
        earliest_date = min(datetime.fromisoformat(m['timestamp']) for m in core_memories)
        latest_date = max(datetime.fromisoformat(m['timestamp']) for m in core_memories)
        print(f"Date range: {earliest_date.date()} to {latest_date.date()}")
    
    emotions = set(m['emotion'] for m in core_memories)
    print(f"Unique emotions: {', '.join(emotions)}")
    
    avg_importance = sum(m['importance'] for m in core_memories) / len(core_memories)
    print(f"Average importance: {avg_importance:.2f}")
    
    print("\nSample core memory:")
    print(json.dumps(core_memories[0], indent=2))
    
    print("\nSample associated memory:")
    print(json.dumps(associated_memories[0], indent=2))

summarize_memories('core_memories.json')