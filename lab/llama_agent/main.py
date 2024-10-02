import os
from groq import Groq

client = Groq(
    api_key="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"
)

def agent_requirements_analyst():
    prompt = (
        "You are a Requirements Analyst. Please outline detailed requirements for a Python program "
        "that demonstrates how AI Agents will perform work in the future. The program should include "
        "features that showcase AI capabilities in automating tasks."
    )
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-groq-70b-8192-tool-use-preview",
    )
    requirements = response.choices[0].message.content
    return requirements

def agent_programmer(requirements):
    prompt = (
        f"You are a Programmer. Based on the following requirements, write the complete Python code:\n\n"
        f"{requirements}\n\n"
        "Ensure the code is well-documented with comments and follows best coding practices."
    )
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-groq-70b-8192-tool-use-preview",
    )
    code = response.choices[0].message.content
    return code

def agent_code_reviewer(code):
    prompt = (
        f"You are a Code Reviewer. Review the following Python code for any errors or improvements. "
        f"Provide the final, corrected code ready to be executed:\n\n{code}"
    )
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-groq-70b-8192-tool-use-preview",
    )
    final_code = response.choices[0].message.content
    return final_code

# Run the agents in sequence
requirements = agent_requirements_analyst()
code = agent_programmer(requirements)
final_code = agent_code_reviewer(code)

# Output the final code to a Python file
with open("ai_agents_future.py", "w") as f:
    f.write(final_code)

print("The final code has been written to 'ai_agents_future.py'.")
